-- @description AI SFX Explorer
-- @version 0.1.0
-- @author AI SFX Explorer contributors
-- @about Localhost client for the AI SFX Explorer retrieval engine.

local script = debug.getinfo(1, 'S').source:sub(2)
local directory = script:match('^(.*[\\/])')
package.path = directory .. 'lib/?.lua;' .. package.path
local api = require('api')

if not reaper.ImGui_GetBuiltinPath then
  error('ReaImGui 0.10+ is required. Install "ReaImGui: ReaScript binding for Dear ImGui" via ReaPack, then restart REAPER.')
end
package.path = reaper.ImGui_GetBuiltinPath() .. '/?.lua;' .. package.path
local ImGui = require('imgui')('0.10')

local ctx = ImGui.CreateContext('AI SFX Explorer',
  ImGui.ConfigFlags_NavEnableKeyboard | ImGui.ConfigFlags_DockingEnable)
local state = {query='', mode='hybrid', results={}, selected=1, status='Ready', preview=nil}

local function stop_preview()
  if state.preview and reaper.CF_Preview_Stop then reaper.CF_Preview_Stop(state.preview) end
  state.preview = nil
end

local function preview(item)
  stop_preview()
  if not reaper.CF_CreatePreview then
    state.status = 'Preview requires the SWS extension'
    return
  end
  local source = reaper.PCM_Source_CreateFromFile(item.path)
  if not source then state.status = 'Could not open source'; return end
  state.preview = reaper.CF_CreatePreview(source)
  reaper.CF_Preview_Play(state.preview)
end

local function search()
  state.status = 'Searching...'
  local response, err = api.search(state.query, state.mode, 50)
  if not response then state.status = 'Backend error: ' .. tostring(err); return end
  state.results = response.results or {}; state.selected = 1
  state.status = string.format('%d results · %.0f ms', #state.results, response.elapsed_ms or 0)
end

local function selected() return state.results[state.selected] end
local function insert(item, new_track)
  if new_track then
    reaper.InsertTrackAtIndex(reaper.CountTracks(0), true)
    reaper.SetOnlyTrackSelected(reaper.GetTrack(0, reaper.CountTracks(0) - 1))
  end
  local segment = item.best_segment
  if segment and reaper.InsertMediaSection and item.duration > 0 then
    reaper.InsertMediaSection(item.path, 0, segment[1] / item.duration,
      segment[2] / item.duration, 0)
  else reaper.InsertMedia(item.path, 0) end
end

local function shortcuts()
  if ImGui.IsKeyPressed(ctx, ImGui.Key_Enter) then
    if ImGui.IsKeyDown(ctx, ImGui.Mod_Ctrl) then
      if selected() then insert(selected(), false) end
    elseif ImGui.IsKeyDown(ctx, ImGui.Mod_Shift) then
      if selected() then insert(selected(), true) end
    else search() end
  elseif ImGui.IsKeyPressed(ctx, ImGui.Key_Space) and selected() then preview(selected())
  elseif ImGui.IsKeyPressed(ctx, ImGui.Key_UpArrow) then state.selected = math.max(1, state.selected - 1)
  elseif ImGui.IsKeyPressed(ctx, ImGui.Key_DownArrow) then state.selected = math.min(#state.results, state.selected + 1)
  elseif ImGui.IsKeyPressed(ctx, ImGui.Key_S) and selected() then
    local response = api.similar(selected().file_id); state.results = response and response.results or state.results
  elseif ImGui.IsKeyPressed(ctx, ImGui.Key_F) and selected() then api.favorite(selected().file_id, true)
  end
end

local function loop()
  ImGui.SetNextWindowSize(ctx, 780, 560, ImGui.Cond_FirstUseEver)
  local visible, open = ImGui.Begin(ctx, 'AI SFX Explorer', true)
  if visible then
    local changed; changed, state.query = ImGui.InputText(ctx, '##query', state.query)
    ImGui.SameLine(ctx); if ImGui.Button(ctx, 'Search') then search() end
    ImGui.SameLine(ctx)
    if ImGui.BeginCombo(ctx, 'Mode', state.mode) then
      for _, mode in ipairs({'hybrid','semantic','metadata'}) do
        if ImGui.Selectable(ctx, mode, state.mode == mode) then state.mode = mode end
      end
      ImGui.EndCombo(ctx)
    end
    ImGui.SeparatorText(ctx, state.status)
    if ImGui.BeginTable(ctx, 'results', 4,
      ImGui.TableFlags_RowBg | ImGui.TableFlags_BordersInnerH | ImGui.TableFlags_ScrollY) then
      ImGui.TableSetupColumn(ctx, 'File'); ImGui.TableSetupColumn(ctx, 'Library')
      ImGui.TableSetupColumn(ctx, 'Duration'); ImGui.TableSetupColumn(ctx, 'Actions')
      ImGui.TableHeadersRow(ctx)
      for index, item in ipairs(state.results) do
        ImGui.TableNextRow(ctx); ImGui.TableNextColumn(ctx)
        if ImGui.Selectable(ctx, item.filename .. '##' .. item.file_id, state.selected == index) then state.selected = index end
        ImGui.TableNextColumn(ctx); ImGui.Text(ctx, item.library or '')
        ImGui.TableNextColumn(ctx); ImGui.Text(ctx, string.format('%.2fs', item.duration or 0))
        ImGui.TableNextColumn(ctx)
        if ImGui.SmallButton(ctx, 'Play##' .. index) then preview(item) end
        ImGui.SameLine(ctx); if ImGui.SmallButton(ctx, 'Insert##' .. index) then insert(item, false) end
      end
      ImGui.EndTable(ctx)
    end
    shortcuts()
    ImGui.TextDisabled(ctx, 'Client log: ' .. api.get_log_path())
    ImGui.End(ctx)
  end
  if open then reaper.defer(loop) else stop_preview() end
end

reaper.defer(loop)
