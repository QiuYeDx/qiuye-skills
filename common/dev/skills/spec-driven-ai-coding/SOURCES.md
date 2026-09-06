# 设计基线与格式参考

核对日期：2026-09-06。第三方资料只用于格式/宿主说明与评估方法；本包具体流程是本次设计，不声称得到官方认证。

1. 旧版代码与本次审计基线：QiuYeDx/qiuye-skills，commit 11ce270ed74c86027334f7aae01805912645e99b。
   https://github.com/QiuYeDx/qiuye-skills/tree/11ce270ed74c86027334f7aae01805912645e99b/common/dev/skills/spec-driven-ai-coding
2. Agent Skills specification：SKILL.md frontmatter、目录、渐进加载建议。
   https://agentskills.io/specification
3. OpenAI Build skills：本地 .agents/skills、可选 agents/openai.yaml、allow_implicit_invocation。
   https://learn.chatgpt.com/docs/build-skills
   原地址 https://developers.openai.com/codex/skills/ 在核对时重定向到上述文档。
4. OpenAI Testing Agent Skills Systematically with Evals：用场景、行为轨迹和结果评价 Skill，而非仅凭主观感觉。
   https://developers.openai.com/blog/eval-skills

未使用第三方运行时依赖或复制第三方 Skill 代码。自动化测试只对本包行为作出实际运行声明。
