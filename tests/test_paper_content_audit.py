import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "paper_content_audit.py"
SPEC = importlib.util.spec_from_file_location("paper_content_audit", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class PaperContentAuditTests(unittest.TestCase):
    def test_visual_validation_accepts_viewbox_and_rejects_fake_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            svg = root / "plot.svg"
            svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600"><path d="M0 0 L800 600"/></svg>', encoding="utf-8")
            fake_png = root / "fake.png"
            fake_png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
            self.assertTrue(AUDIT.visual_file_is_readable(svg))
            self.assertFalse(AUDIT.visual_file_is_readable(fake_png))

    def test_strict_cli_cannot_disable_hard_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paper = root / "paper.md"
            paper.write_text("# 问题一\n\n正文。\n", encoding="utf-8")
            ledger = root / "ledger.json"
            ledger.write_text(json.dumps({"models": []}), encoding="utf-8")
            benchmark = root / "benchmark.json"
            benchmark.write_text(json.dumps({
                "samples": [{"id": "sample"}],
                "current_gaps": ["gap"],
                "forbidden_terms": ["样本作者"],
            }, ensure_ascii=False), encoding="utf-8")
            command = [
                sys.executable, "-B", str(SCRIPT), str(paper),
                "--project-root", str(root),
                "--derivation-ledger", str(ledger),
                "--benchmark-gap", str(benchmark),
                "--min-equations", "0", "--min-figures", "0",
                "--min-references", "0", "--min-decision-traces", "0",
                "--strict",
            ]
            completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(completed.returncode, 1)
            report = json.loads(completed.stdout)
            codes = {item["code"] for item in report["issues"] if item["severity"] == "FAIL"}
            self.assertIn("equation_count_below_target", codes)
            self.assertIn("figure_count_below_target", codes)
            self.assertIn("reference_count_below_target", codes)
            self.assertIn("decision_log_not_supplied", codes)
            self.assertIn("final_docx_not_supplied", codes)

    def test_rejects_known_bad_patterns(self):
        text = """# 问题一
往届 A028 获奖论文用于核对数量级。
$$e_ij=10^-5$$
正文仍残留 e_ij 与 10^-5 两处纯文本数学表达式。
![图1 结果](figures/a.png)
该图用于说明本节的几何关系或数值结果。
# 参考文献
[1] 获奖论文A028.
"""
        findings, metrics = AUDIT.audit_text(text, True, 15, 12, 8)
        codes = {item["code"] for item in findings if item["severity"] == "FAIL"}
        self.assertIn("double_dollar", codes)
        self.assertIn("plain_text_math", codes)
        self.assertIn("contest_context_leak", codes)
        self.assertIn("empty_figure_commentary", codes)
        self.assertIn("equation_count_below_target", codes)
        self.assertIn("figure_count_below_target", codes)
        self.assertIn("reference_count_below_target", codes)
        self.assertEqual(metrics["figures"], 1)

    def test_complete_fixture_passes_strict_semantic_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "results").mkdir()
            (root / "figures").mkdir()
            evidence_payload = {"metric": "relative_error", "baseline": 1.0, "result": 0.95, "levels": [-0.2, 0, 0.2]}
            (root / "results" / "evidence.json").write_text(json.dumps(evidence_payload), encoding="utf-8")
            for name in ("method_a", "method_b", "decision_1", "decision_2", "decision_3", "parameter_p1", "parameter_p2", "model_flat", "model_curved", "boundary_full", "boundary_clip"):
                (root / "results" / f"{name}.json").write_text(json.dumps({"name": name, "value": 0.5}), encoding="utf-8")
            for index in range(1, 13):
                svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600"><polyline points="0,500 400,{500-index*10} 800,{100+index*5}"/><text x="20" y="40">figure-{index}</text></svg>'
                (root / "figures" / f"f{index}.svg").write_text(svg, encoding="utf-8")

            parts = [
                "# 问题一：模型建立",
                "## 交叉验证",
                "两种独立计算方法采用相同输入，以相对误差评价一致性。",
                "## 灵敏度分析",
                "参数敏感性、模型敏感性和边界规则敏感性分别改变连续参数、假设与边界。",
                "## 物理目标与优化目标",
                "物理目标与代理目标的关系由对比实验和权衡曲线检验。",
                "## 工程裕度",
                "安全裕度按上限与最不利实际值计算，并讨论测量误差。",
            ]
            equations = [
                r"x_1=a+b", r"x_2=ab", r"x_3=\frac{a}{b}", r"x_4=\sqrt{a^2+b^2}",
                r"x_5=\sum_{i=1}^{n}a_i", r"x_6=\int_0^1 f(t)\,\mathrm{d}t", r"x_7=\mathbf{A}\mathbf{x}-\mathbf{b}",
                r"x_8=\lVert\mathbf{x}\rVert_2", r"x_9=\exp(-a t)", r"x_{10}=\log(1+a)",
                r"x_{11}=\max\{a,b\}", r"x_{12}=\min\{a,b\}", r"x_{13}=\frac{\partial f}{\partial a}",
                r"x_{14}=\frac{\mathrm{d}g}{\mathrm{d}t}", r"x_{15}=\operatorname{RMSE}(\hat y,y)",
            ]
            for number, equation in enumerate(equations, 1):
                parts.extend([
                    rf"\[{equation},\tag{{{number}}}\]",
                    f"式({number})由前一状态递推得到，用于计算第{number}个中间量；代入1后结果为{number}，量纲保持一致。",
                ])
            for number in range(1, 13):
                parts.extend([
                    f"![图{number} 真实结果](figures/f{number}.svg)",
                    f"图中结果显示第{number}组在参数为{number}时达到最大值{number + 1}，随后下降至{number * 0.8:.1f}，相对降幅为20%。该转折由约束逐渐活跃导致，异常区域集中在边界附近，说明继续增大参数不能改善物理目标；工程上应采用当前范围，并把边界外区域列为模型失效风险。",
                ])
            parts.append("# 参考文献")
            references = [
                "Nocedal J, Wright S J. Numerical Optimization[M]. Springer, 2006.",
                "Timoshenko S P, Woinowsky-Krieger S. Theory of Plates and Shells[M]. McGraw-Hill, 1959.",
                "Saltelli A, Ratto M, Andres T. Global Sensitivity Analysis[M]. Wiley, 2008.",
                "Montgomery D C. Design and Analysis of Experiments[M]. Wiley, 2017.",
                "Higham N J. Accuracy and Stability of Numerical Algorithms[M]. SIAM, 2002.",
                "Boyd S, Vandenberghe L. Convex Optimization[M]. Cambridge University Press, 2004.",
                "Hastie T, Tibshirani R, Friedman J. The Elements of Statistical Learning[M]. Springer, 2009.",
                "ISO. Guide to the Expression of Uncertainty in Measurement[S]. ISO, 2008.",
            ]
            parts.extend(f"[{number}] {entry}" for number, entry in enumerate(references, 1))
            text = "\n\n".join(parts)
            text_findings, text_metrics = AUDIT.audit_text(text, True, 15, 12, 8, root)

            ledger = {
                "models": [{
                    "model_id": "q1_opt",
                    "question": "问题一",
                    "model_type": "optimization",
                    "reality_mapping": "把工程控制量映射为决策变量",
                    "variables": [{"symbol": "x", "meaning": "控制量", "unit": "m", "kind": "scalar"}],
                    "assumptions": [{"statement": "局部线性", "condition": "位移足够小", "error_scale": "二阶余项小于1%"}],
                    "derivation_steps": [
                        {"step": 1, "input": "定义", "operation": "守恒", "output_equation": 1, "purpose": "建立关系"},
                        {"step": 2, "input": "式(1)", "operation": "代入", "output_equation": 2, "purpose": "得到目标"},
                    ],
                    "algorithm_steps": [
                        {"step": 1, "action": "初始化", "purpose": "构造可行点", "failure_condition": "无可行点"},
                        {"step": 2, "action": "求解", "purpose": "优化目标", "failure_condition": "不收敛"},
                    ],
                    "objective": "最小化代理误差",
                    "constraints": ["控制量不超过上限"],
                    "hard_constraints": ["displacement_upper"],
                    "physical_goal": "最大化物理效率",
                    "optimized_goal": "最小化代理误差",
                    "goal_relationship": "代理误差为物理效率损失的二阶近似",
                    "direct_physical_objective_trial": {
                        "objective": "最大化物理效率",
                        "result": "效率为95%",
                        "comparison": "比代理目标方案高0.3个百分点",
                        "evidence": "results/evidence.json",
                    },
                    "tradeoff_evidence": "results/evidence.json",
                    "data_pipeline": {"preprocessing": [], "feature_selection": None, "parameter_selection": None, "evaluation_metrics": []},
                    "numerical_example": {"inputs": "x=1 m", "calculation": "1+1", "result": "2 m"},
                    "validation": ["独立方法相对误差0.5%"],
                    "evidence_paths": ["results/evidence.json"],
                    "ambiguity": "边界积分口径存在歧义",
                    "cross_validation": {
                        "methods": [
                            {"name": "解析积分", "principle": "闭式积分", "result": "0.951", "evidence": "results/method_a.json"},
                            {"name": "数值追迹", "principle": "离散射线求和", "result": "0.946", "evidence": "results/method_b.json"},
                        ],
                        "comparison_metric": "相对误差",
                        "result": "0.5%",
                        "difference_reason": "离散误差",
                        "selection": "采用数值追迹并以解析解校验",
                    },
                    "sensitivity_fallback": None,
                }],
                "sensitivity": {
                    "parameter": [
                        {"name": "p1", "levels": [-0.2, 0, 0.2], "result_summary": "关键输出变化3%", "evidence": "results/parameter_p1.json"},
                        {"name": "p2", "levels": [-0.2, 0, 0.2], "result_summary": "关键输出变化5%", "evidence": "results/parameter_p2.json"},
                    ],
                    "model_variants": [
                        {"name": "平面", "result_summary": "误差为2%", "evidence": "results/model_flat.json"},
                        {"name": "曲面", "result_summary": "误差为1%", "evidence": "results/model_curved.json"},
                    ],
                    "boundary_variants": [
                        {"name": "完全纳入", "result_summary": "纳入80个单元", "evidence": "results/boundary_full.json"},
                        {"name": "面积裁剪", "result_summary": "纳入76个单元", "evidence": "results/boundary_clip.json"},
                    ],
                    "conclusions": "在给定范围内稳定，范围外失效",
                },
                "engineering_margins": [{
                    "constraint_id": "displacement_upper",
                    "constraint": "位移上限",
                    "constraint_type": "upper",
                    "limit": 1.0,
                    "actual": 0.8,
                    "unit": "m",
                    "margin_percent": 20.0,
                    "evidence": "results/evidence.json",
                    "uncertainty_discussion": "测量误差小于0.01 m",
                }],
                "required_visuals": [
                    {"type": "technical_route", "file": "figures/f1.svg", "data_source": "流程", "claim": "总体路线"},
                    {"type": "subproblem_flow", "file": "figures/f2.svg", "data_source": "算法", "claim": "子问流程"},
                    {"type": "model_comparison", "file": "figures/f3.svg", "data_source": "结果", "claim": "方案权衡"},
                    {"type": "cumulative_distribution", "file": "figures/f4.svg", "data_source": "结果", "claim": "累积分布"},
                ],
                "figure_manifest": [
                    {
                        "file": f"figures/f{number}.svg",
                        "question": "问题一",
                        "data_source": "results/evidence.json",
                        "claim": f"支持第{number}项定量结论",
                        "analysis_anchor": f"图{number} 真实结果",
                    }
                    for number in range(1, 13)
                ],
            }
            ledger_path = root / "derivation-ledger.json"
            ledger_path.write_text(json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
            ledger_findings, ledger_metrics = AUDIT.audit_derivation_ledger(ledger_path, root, True)
            self.assertEqual(set(text_metrics["figure_files"]), set(ledger_metrics["manifest_figure_files"]))
            self.assertTrue(all(anchor in text for anchor in ledger_metrics["manifest_analysis_anchors"]))

            decisions = []
            for number in range(3):
                decisions.append({
                    "question": "问题一",
                    "initial_option": f"方案{number}",
                    "observed_problem": "误差偏大",
                    "evidence": [f"results/decision_{number + 1}.json"],
                    "alternatives": ["替代方案"],
                    "final_choice": "替代方案",
                    "reason": "相对误差更低",
                })
            decision_path = root / "decision-traces.json"
            decision_path.write_text(json.dumps(decisions, ensure_ascii=False), encoding="utf-8")
            decision_findings, _ = AUDIT.audit_decision_log(decision_path, root, True, 3)

            benchmark_path = root / "benchmark-gap.json"
            benchmark_path.write_text(json.dumps({
                "samples": [{
                    "id": "internal-1",
                    "title": "样本专有标题",
                    "authors": ["样本作者甲"],
                    "result_tokens": ["专有结果95.7%"],
                    "body_pages": 20,
                    "appendix_pages": 10,
                }],
                "current_gaps": ["需补交叉验证"],
                "forbidden_terms": ["internal-1", "样本专有标题", "样本作者甲", "专有结果95.7%"],
            }, ensure_ascii=False), encoding="utf-8")
            benchmark_findings, _ = AUDIT.audit_benchmark_gap(benchmark_path)

            all_findings = text_findings + ledger_findings + decision_findings + benchmark_findings
            failures = [item for item in all_findings if item["severity"] == "FAIL"]
            self.assertEqual(failures, [], failures)


    def test_table_numbering_catches_duplicate_and_dangling(self):
        text = """结果如表2所示。

| 符号 | 含义 |
|---|---|
| x | 变量 |

  : 表 1主要符号

第二张表也以表1被引用。

| 方案 | 值 |
|---|---|
| a | 1 |

  : 对照表 {#tab:second}

表[1](#tab:second)显示两组差异，结论按表3执行。
"""
        findings = AUDIT.audit_table_references(text, True)
        codes = {item["code"] for item in findings}
        self.assertIn("duplicate_table_caption_number", codes)
        self.assertIn("dangling_table_reference", codes)

    def test_table_numbering_clean_paper_passes(self):
        text = """结果如表1所示。

| a | b |
|---:|---:|
| 1 | 2 |

  : 表 1主表

其余见表2。

| c | d |
|---|---|
| 3 | 4 |

  : 表 2对照表
"""
        findings = AUDIT.audit_table_references(text, True)
        self.assertEqual([item for item in findings if item["severity"] == "FAIL"], [])

    def test_results_policy_cross_reference_flags_unrun_policy(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "results").mkdir()
            (root / "results" / "backtest.csv").write_text(
                "round,policy,rmse\n1,hybrid,0.1\n1,random,0.2\n1,pure_exploitation,0.3\n1,maximin,0.4\n",
                encoding="utf-8",
            )
            disclosed = "混合策略优于随机策略；只追求均值会集中选点，maximin 备用方案未启用。"
            ok_findings, metrics = AUDIT.audit_results_policy_cross_reference(root, disclosed)
            self.assertEqual([item for item in ok_findings if item["severity"] == "FAIL"], [])
            self.assertEqual(len(metrics["results_policy_values"]), 4)

            hidden = "混合策略优于随机策略，但不比较只追求不确定性的策略。"
            bad_findings, _ = AUDIT.audit_results_policy_cross_reference(root, hidden)
            bad_codes = {item["code"] for item in bad_findings}
            self.assertIn("text_describes_unrun_policy", bad_codes)
            self.assertIn("results_policy_not_disclosed", bad_codes)

    def test_docx_duplicate_heading_detected(self):
        import io
        import zipfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            namespace = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
            body = (
                '<w:document ' + namespace + '><w:body>'
                '<w:p><w:pPr><w:pStyle w:val="1"/></w:pPr><w:r><w:t>附录 D代码</w:t></w:r></w:p>'
                '<w:p><w:pPr><w:pStyle w:val="1"/></w:pPr><w:r><w:t>附录 D　代码</w:t></w:r></w:p>'
                '<w:p><w:pPr><w:pStyle w:val="2"/></w:pPr><w:r><w:t>正常小节</w:t></w:r></w:p>'
                '</w:body></w:document>'
            )
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as archive:
                archive.writestr("word/document.xml", body)
            path = root / "dup.docx"
            path.write_bytes(buffer.getvalue())
            findings, _ = AUDIT.audit_final_docx(path)
            codes = {item["code"] for item in findings}
            self.assertIn("duplicate_docx_heading", codes)


if __name__ == "__main__":
    unittest.main()
