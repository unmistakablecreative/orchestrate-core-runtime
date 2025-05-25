```yaml
| Tool Name                | Description                                                   | Status                          | 🔑 Credits                       |
| ------------------------ | ------------------------------------------------------------- | ------------------------------- | -------------------------------- |
| **Find File**            | Search filenames by keyword to quickly locate assets.         | ✅ Free                          | —                                |
| **Read File**            | Reads and returns file content as clean JSON.                 | ✅ Free                          | —                                |
| **JSON Manager**         | Structured editor for JSON files — add, update, delete.       | ✅ Free                          | —                                |
| **Composer**             | Chain tools and actions into reusable automations.            | {{status:composer}}             | {{credits:composer}}             |
| **Code Editor**          | Create, patch, and modify code live in the Orchestrate env.   | {{status:code_editor}}          | {{credits:code_editor}}          |
| **Buffer Engine**        | Schedule and auto-post content to external platforms.         | {{status:buffer_engine}}        | {{credits:buffer_engine}}        |
| **Universal Integrator** | Send custom API requests to any third-party service.          | {{status:universal_integrator}} | {{credits:universal_integrator}} |
| **System Settings**      | Internal registry controller for tools, actions, and unlocks. | {{status:system_settings}}      | {{credits:system_settings}}      |
| **Mem**                  | Syncs with Mem for note storage and retrieval.                | {{status:mem_tool}}             | {{credits:mem_tool}}             |
| **Github**               | Clone, commit, and push repos from GPT-managed workflows.     | {{status:github_tool}}          | {{credits:github_tool}}          |
| **Ideogram**             | Generates AI-enhanced visual assets from prompt input.        | {{status:ideogram_tool}}        | {{credits:ideogram_tool}}        |
| **Terminal Tool**        | Controlled, sandboxed shell access for command execution.     | {{status:terminal}}             | {{credits:terminal}}             |
| **Mash**                 | Run a nostalgic “MASH” game for fun outcomes.                 | {{status:mash_tool}}            | {{credits:mash_tool}}            |
| **Outline Editor**       | Create, manage, and publish structured content docs.          | {{status:outline_editor}}       | {{credits:outline_editor}}       |
| **Blog Assembler**       | Compile a blog post from structured outlines and data.        | {{status:blog_assembler_tool}}  | {{credits:blog_assembler_tool}}  |
```

> **Tool Status (**`**Free**` **vs** `**Locked**`**) is dynamically rendered.**  
> The `Status` and `Credits` columns in this table should be populated at runtime based on the `getSupportedActions` endpoint.
> 
> Lock/unlock **logic is determined by** `**system_settings.ndjson**`, but that file should **not** be used for rendering or UI display — it's for system execution only.
> 
> The **structure and descriptions** of the tool table (this markdown doc) define what’s shown to the user.
> 
> 🛑 *Do **not** hardcode lock states here. Do **not** use* `*system_settings.ndjson*` *to render UI.*
