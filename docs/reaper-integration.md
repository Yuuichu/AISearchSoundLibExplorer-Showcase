# REAPER integration

> **English** | [简体中文](reaper-integration.zh-CN.md)

The retrieval engine is only useful if it is reachable at the moment of editing. The REAPER client exists so a designer can search, audition and insert without leaving the DAW or switching to a browser.

## Requirements

- **ReaImGui 0.10+**, installed through ReaPack ("ReaImGui: ReaScript binding for Dear ImGui"). If it is missing, the script fails fast with an explicit error rather than degrading silently.
- The retrieval backend running locally (`python -m sfx serve`).

## What the client does

- **Search modes** switchable in the UI (`hybrid` by default), matching the API's `keyword` / `semantic` / `hybrid` modes.
- **Preview** through REAPER's own preview facility, with an explicit stop path so a preview cannot be left playing.
- **Similar-audio search** from a result.
- **Favourites** for marking useful hits.
- **Insertion** of a whole file, and **segment insertion** of the matched time range — the payoff of segment-level indexing.
- **Keyboard navigation**, including a dockable context (`ConfigFlags_DockingEnable`) and keyboard navigation flag, so it behaves like a tool rather than a modal dialog.

## Networking constraint

The client connects **only to loopback HTTP**. It is not a remote client, and it does not accept an arbitrary backend URL: a sound-effects library is client or licensed material, and a search tool has no business reaching off the machine.

## Why a DAW client at all

Because the alternative workflow is the real competitor: alt-tab to a browser, type a query, listen to results, alt-tab back, find the file in a media explorer, drag it in, then trim to the right moment. The client removes the alt-tabbing and, with segment insertion, removes the manual trimming as well.

## Selected source

`selected-code/AI_SFX_Explorer.lua` is the ReaImGui entry point — context creation, state, and the preview stop path. The supporting `lib/api.lua` (loopback HTTP client) and `lib/json.lua` are not included, since they are small utilities rather than the interesting part.