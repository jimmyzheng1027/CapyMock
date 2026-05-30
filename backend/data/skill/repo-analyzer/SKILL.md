---
name: repo-analyzer
description: |
  Analyze a GitHub repository to produce a structured learning report for job seekers.
  Covers: project overview, architecture, design patterns, best practices, and 15 project-specific interview questions.
  Use this skill when the user provides a GitHub URL and wants to understand, learn from, or prepare interview questions about a repository.
  Triggers on: "analyze this repo", "help me understand this project", "generate interview questions for this repo",
  "分析这个仓库", "帮我理解这个项目", or any GitHub URL paired with a learning/analysis intent.
---

## Workflow

The analysis has 5 phases. Follow them in order. Do not skip ahead.

**Cache:** Completed analyses are checked by the API before this agent runs. If you are invoked, proceed with a fresh analysis — do not call `query_github_analysis`.

### Phase 0: Load this skill

If you have not already loaded the full workflow in this session, call:

```
read_skill(skill_id="repo-analyzer")
```

Follow the returned content for all phases below.

### Phase 1: Clone the Repository

Use `clone_repo` to shallow clone the repository:

```
clone_repo(analysis_id="<id>", url="<repo-url>")
```

If clone fails, report the error and stop. Do not attempt to guess repository contents.

On success, the result contains `repo_path` for logging only. **All file tools automatically scope to that clone** — use paths **relative to the repository root** from here on (not the `storage/repo/...` prefix).

### Phase 2: Scan Metadata

Gather high-level project information. This phase gives you the context needed to make smart decisions in Phase 3.

**2a + 2b: Batch these calls together.** `list_directory`, config file, and README have no dependencies — call them all in one turn:

```
list_directory(path=".", max_depth=5)
read_file(path="pyproject.toml")   # or package.json, go.mod, etc.
read_file(path="README.md")
```

The `list_directory` response includes a `directoryTree` field with the structured tree. Use this directly — do NOT recreate the tree yourself.

For the config file, pick the primary one based on language:
- Python: `pyproject.toml`, `setup.py`, `requirements.txt`
- Node/JS/TS: `package.json`
- Go: `go.mod`
- Rust: `Cargo.toml`
- Java: `pom.xml`, `build.gradle`

### Phase 3: Read Key Files (LLM-Driven Selection)

This is the most important phase. Based on what you learned in Phase 2, decide which files to read.

**Selection strategy:**

You have seen the directory tree, the config file, and the README. Now think like an architect: "Which files would I need to read to truly understand this project?"

Prioritize in this order:
1. **Entry points** — the files where execution starts (main.py, main.go, index.ts, app.py, server.py, cmd/main.go, main.rs)
2. **Core module files** — the main files of the 3-5 most important modules/packages. Look at the directory structure: which folders seem like the core business logic?
3. **Routing / API definitions** — how are endpoints or commands defined?
4. **Type definitions / models / schemas** — the data structures that define the domain
5. **Configuration / middleware / plugins** — how is the app configured and extended?
6. **Test examples** — 1-2 test files that show testing patterns and conventions

Read **15-25 files** total. Use `read_file` with paths **relative to the repo root** (e.g. `src/main.py`, not `storage/repo/<id>/src/main.py`). Read the full file — do not truncate. If a file is extremely long (>500 lines), read the first 300 lines, which usually contains the key interfaces and patterns.

**Batch reads: 3-5 files per turn.** Select your files first, then call multiple `read_file` in one turn. This reduces steps from ~20 to ~5. Example:

```
read_file(path="src/main.py")
read_file(path="src/routes.py")
read_file(path="src/models.py")
read_file(path="src/config.py")
```

**Avoid reading:**
- Lock files (package-lock.json, yarn.lock, poetry.lock, Cargo.lock)
- Auto-generated code (.generated.*, *.pb.go, *_generated.*)
- Minified or bundled files
- Build output (dist/, build/)
- Vendored dependencies (vendor/, node_modules/)

**Why this phase matters:** The quality of your analysis depends entirely on which files you choose to read. A poor file selection leads to a shallow, inaccurate report. Take time to reason about the project structure before deciding.

### Phase 4: Analyze and Output

Using all the information gathered (metadata + file contents), produce a single JSON output.

Think through each layer carefully before writing. Do not rush.

### Phase 5: Save the Result

After producing the JSON output in Phase 4, save it to the database:

```
save_repo_analysis(analysis_id="<analysis-id>", result_json="<your-json-output>")
```

Use the same `analysis_id` that was used for `clone_repo`. The `result_json` should be the complete JSON string from Phase 4.

If save fails, include the error in your output but do not re-attempt.

---

## Output Format

Output a single JSON object. No markdown code fences, no explanation text before or after. The JSON must be valid and parseable.

The output has two levels: **overview** and **deep**. Always produce both.

### Overview Level Fields

```json
{
  "id": "owner-repo-name",
  "fullName": "owner/repo-name",
  "owner": "owner",
  "repoName": "repo-name",
  "description": "One-sentence description from README or your understanding",
  "url": "https://github.com/owner/repo",
  "analyzedAt": "ISO 8601 timestamp",
  "techTags": ["React", "TypeScript", "Zustand", "Vite"],
  "directoryTree": { ... },
  "highlights": [ ... ],
  "suggestions": [ ... ],
  "questions": [ ... ]
}
```

**Field details:**

- `techTags`: List 4-8 key technologies. Include language, framework, major libraries, build tools, testing frameworks.

- `directoryTree`: Use the `directoryTree` from the `list_directory` tool response directly. Do NOT recreate it.

- `highlights`: 3-5 notable strengths of the project. Each item:
  ```json
  { "type": "positive", "text": "代码结构清晰：模块划分合理，目录组织遵循最佳实践" }
  ```
  Use `type: "positive"` for strengths. Use Chinese for the text.

- `suggestions`: 3-5 actionable improvement suggestions. Use Chinese.

- `questions`: Exactly 15 interview questions. See "Interview Questions" section below.

### Deep Analysis Level Fields

In addition to all overview fields, include:

```json
{
  ...overview fields...,
  "sections": [ ... ],
  "codeSnippets": [ ... ]
}
```

- `sections`: Array of 5 analysis sections. Each section:
  ```json
  {
    "id": "architecture",
    "title": "项目架构分析",
    "icon": "layers",
    "content": "<h4>整体架构</h4><p>HTML content...</p>"
  }
  ```

  The 5 sections (use these exact IDs and icons):
  1. `architecture` / `layers` — 项目架构分析: overall architecture, data flow, module relationships
  2. `code-quality` / `check-circle` — 代码质量评估: type safety, code conventions, test coverage
  3. `performance` / `zap` — 性能分析: build output, runtime performance, optimization opportunities
  4. `security` / `shield` — 安全性分析: dependency security, input validation, secrets management
  5. `summary` / `star` — 综合评价与建议: overall assessment, core strengths, improvement directions

  The `content` field contains HTML. Use `<h4>` for subheadings, `<p>` for paragraphs, `<ul>/<li>` for lists, `<code>` for inline code, `<strong>` for emphasis. Write in Chinese.

- `codeSnippets`: 2-4 important code excerpts that illustrate key patterns. Each snippet:
  ```json
  {
    "id": "snippet-1",
    "title": "全局状态管理 — Zustand Store",
    "language": "typescript",
    "code": "// actual code from the repository",
    "description": "使用 Zustand 管理全局状态，接口定义清晰，操作简洁。"
  }
  ```
  Use real code from the files you read, not invented examples. Write title and description in Chinese.

---

## Interview Questions

Generate exactly 15 questions. These must be **specific to this repository**, not generic algorithm or framework questions.

**What makes a good question:**
- It references specific code, architecture decisions, or patterns from THIS project
- It tests understanding of WHY things were designed this way, not just WHAT they do
- It would make sense in an interview where the candidate listed this project on their resume

**What to avoid:**
- Generic algorithm questions ("implement quicksort")
- Framework trivia ("what is the virtual DOM?")
- Questions that could apply to any project ("describe your testing strategy")

**Question categories (distribute across these):**
1. Architecture decisions: "项目为什么选择 X 而不是 Y？"
2. Design patterns: "解释一下这个项目中的依赖注入是如何工作的"
3. Code comprehension: "描述一个请求从入口到响应的完整流程"
4. Trade-offs: "这种设计方案有什么局限性？"
5. Extension: "如果要给这个项目添加 X 功能，你会怎么设计？"

Each question object:
```json
{
  "q": "FastAPI 使用装饰器定义路由而不是配置文件，这种设计的优劣是什么？",
  "a": "从可读性、关注点分离、装饰器元编程等角度讨论，对比 Flask/Express 的路由方式。"
}
```

The `a` field is a brief answer hint — key points the candidate should cover. Write both `q` and `a` in Chinese.

---

## Cleanup

After outputting the JSON, the cloned source is retained in `storage/repo/<id>/` for potential reuse. Do NOT delete it.

---

## Error Handling

| Situation | Action |
|---|---|
| Invalid or unreachable URL | Output JSON with an `error` field, stop |
| Private repository | Output JSON with an `error` field explaining private repos cannot be analyzed |
| Empty or minimal repository | Output JSON with an `error` field |
| Repository too large (>5000 files) | Warn in `suggestions`, proceed with deeper pruning of directory tree |
| Non-code repository (docs only, assets only) | Output JSON with an `error` field |

When encountering an error, still output valid JSON:
```json
{
  "error": "无法分析该仓库：仓库为私有仓库，无法克隆",
  "url": "https://github.com/..."
}
```

## Large Repository Protection

If the repository has many files (>5000), proceed with caution:
- Use a smaller `max_depth` (2 instead of 3) for `list_directory`
- Be more selective in Phase 3 (read fewer files)
- Warn about the repository size in `suggestions`
