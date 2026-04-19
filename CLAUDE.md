# Digger Sim — Claude Project Guide

Digger Sim is a digger simulator game for kids. This file orients Claude agents working on this codebase and routes work to the correct department sub-agent.

## Project Structure

```
digger-sim/
├── CLAUDE.md
├── .claude/
│   └── agents/
│       ├── creative-director.md
│       ├── design.md
│       ├── art.md
│       ├── programming.md
│       └── qa.md
├── src/
│   ├── game/          # Core game logic
│   ├── ui/            # UI components
│   └── assets/        # Asset references
└── tests/             # QA test suites
```

## Department Agents

Route work to the appropriate sub-agent based on task type:

| Department | Agent | Handles |
|---|---|---|
| Creative Director | `creative-director` | Vision, cross-department decisions, final approval |
| Design | `design` | Game mechanics, levels, systems design docs |
| Art | `art` | Visual assets, style guides, animations |
| Programming | `programming` | Code implementation, architecture, performance |
| QA | `qa` | Testing, bug reports, acceptance criteria |

## Routing Guide

- **"Does this feel fun / is this the right direction?"** → creative-director
- **"How should this mechanic work?"** → design
- **"How should this look / what style?"** → art
- **"Implement / fix / refactor this"** → programming
- **"Is this working correctly?"** → qa

## Tech Stack

- Language: TypeScript / JavaScript
- Runtime: Browser (HTML5 Canvas)
- Target audience: Kids (ages 4–10)

## Key Principles

- Keep interactions simple and tactile — kids should grasp controls immediately
- Visuals should be bright, chunky, and satisfying
- No fail states — digger sim is about exploration and joy, not challenge
- Performance matters: target 60fps on low-end tablets
