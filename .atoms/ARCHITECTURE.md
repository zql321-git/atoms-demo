---
last_updated: 2026-09-27T05:31:11Z
---

# Architecture Design

## System Overview
React 单页：前端 client.ai.gentxt(claude-opus-4.6) 流式生成 HTML → iframe srcDoc 实时预览 → 保存到 Atoms Cloud 表 page_versions（user_id, version_no, prompt, html），侧栏切换历史版本。关键文件：app/frontend/src/pages/Index.tsx。

## Tech Stack

## Module Design
| Module | Responsibility | Key Files |
|--------|---------------|-----------|

## Tech Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|

## File Tree Plan

## Implementation Guide

