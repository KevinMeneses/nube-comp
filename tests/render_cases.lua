-- Carga Nube Comp en una pestaña nueva, renderiza cada caso y cierra la pestaña.
-- Uso: REAPER -nonewinst tests/render_cases.lua   (escribe tests/out/*.wav y tests/out/log.txt)
local ROOT = debug.getinfo(1, "S").source:match("^@(.*)/[^/]*$")
local OUT = ROOT .. "/out"
os.execute('mkdir -p "' .. OUT .. '"')
local logf = io.open(OUT .. "/log.txt", "w")
local function log(...) local t = {} for _, v in ipairs({...}) do t[#t+1] = tostring(v) end logf:write(table.concat(t, " "), "\n") logf:flush() end

-- slider N (1..25) = parámetro N-1. Los sliders con forma :log=mid van normalizados 0..1
local LOGP = {[2] = {1, 30, 4}, [4] = {0.01, 300, 10}, [5] = {5, 3000, 150}, [19] = {20, 1000, 120}, [20] = {1000, 20000, 5000}, [21] = {100, 10000, 1000}}
local function to_norm(s, v)
  local mn, mx, mid = table.unpack(LOGP[s])
  local sr = (mx - mn) / (mid - mn) - 1; local r = sr * sr
  return math.log((v - mn) / (mx - mn) * (r - 1) + 1) / math.log(r)
end
-- base para las curvas estáticas: Limpio, ataque 0.1 ms, release 500 ms, rodilla 0
local function P(t)
  local r = {[7] = 0, [4] = 0.1, [5] = 500, [3] = 0, [8] = 0}
  for k, v in pairs(t) do r[k] = v end
  return r
end
local HARD = {[1] = -20, [2] = 4}
local function with(a, b) local r = {} for k, v in pairs(a) do r[k] = v end for k, v in pairs(b) do r[k] = v end return r end

local CASES = {
  {"below_null",  "sine1k_m30.wav", P{[1] = -20, [2] = 4}},
  {"hard_r4",     "sine1k_m6.wav",  P(HARD)},
  {"soft_knee",   "sine1k_m6.wav",  P{[1] = -10, [2] = 4, [3] = 12}},
  {"r_inf",       "sine1k_m6.wav",  P{[1] = -20, [2] = 30}},
  {"range3",      "sine1k_m6.wav",  P(with(HARD, {[11] = 3}))},
  {"makeup6",     "sine1k_m6.wav",  P(with(HARD, {[12] = 6}))},
  {"automk",      "sine1k_m6.wav",  P(with(HARD, {[13] = 1}))},
  {"mix50",       "sine1k_m6.wav",  P(with(HARD, {[14] = 50}))},
  {"rms_det",     "sine1k_m6.wav",  P(with(HARD, {[15] = 1}))},
  {"link100",     "lr.wav",         P(HARD)},
  {"link0",       "lr.wav",         P(with(HARD, {[16] = 0}))},
  {"ms_link",     "lr.wav",         P(with(HARD, {[17] = 1}))},
  {"solo_mid",    "sine1k_m6.wav",  P(with(HARD, {[17] = 2}))},
  {"solo_side",   "sine1k_m6.wav",  P(with(HARD, {[17] = 3}))},
  {"ext_sc",      "sidechain4.wav", P{[1] = -30, [2] = 4, [4] = 1, [5] = 50, [18] = 1}, 4},
  {"lf_nohpf",    "sine50_m6.wav",  P(HARD)},
  {"lf_hpf300",   "sine50_m6.wav",  P(with(HARD, {[19] = 300}))},
  {"sclisten",    "sine50_m6.wav",  P(with(HARD, {[19] = 300, [23] = 1}))},
  {"focus",       "sine1k_m30.wav", P{[1] = -26, [2] = 4, [21] = 1000, [22] = 12}},
  {"delta",       "sine1k_m6.wav",  P(with(HARD, {[24] = 1}))},
  {"timing",      "step.wav",       P{[1] = -30, [2] = 4, [4] = 10, [5] = 100}},
  {"hold",        "step.wav",       P{[1] = -30, [2] = 4, [4] = 10, [5] = 100, [10] = 200}},
  {"la_off",      "burst.wav",      P{[1] = -20, [2] = 30, [4] = 1, [5] = 200}},
  {"la_5",        "burst.wav",      P{[1] = -20, [2] = 30, [4] = 1, [5] = 200, [9] = 5}},
  {"color0",      "sine1k_m6.wav",  P{[1] = 0, [2] = 1}},
  {"color_fet",   "sine1k_m6.wav",  P{[1] = 0, [2] = 1, [7] = 3, [8] = 50}},
  {"color_tubo",  "sine1k_m6.wav",  P{[1] = 0, [2] = 1, [7] = 4, [8] = 50}},
}
for st = 0, 4 do
  CASES[#CASES + 1] = {"style" .. st, "step.wav", {[7] = st, [1] = -30, [2] = 4, [3] = 0, [4] = 5, [5] = 100}}
  CASES[#CASES + 1] = {"style" .. st .. "_auto", "step.wav", {[7] = st, [1] = -30, [2] = 4, [4] = 5, [5] = 100, [6] = 1, [8] = 60}}
end
for p = 1, 25 do local sc = p == 8 or p == 21; CASES[#CASES + 1] = {"preset" .. p, sc and "sidechain4.wav" or "step.wav", {[25] = p}, sc and 4 or 2} end

reaper.Main_OnCommand(40859, 0) -- nueva pestaña
reaper.GetSetProjectInfo(0, "PROJECT_SRATE", 48000, true)
reaper.GetSetProjectInfo(0, "PROJECT_SRATE_USE", 1, true)
reaper.InsertTrackAtIndex(0, false); local tr = reaper.GetTrack(0, 0)
local item = reaper.AddMediaItemToTrack(tr)
local take = reaper.AddTakeToMediaItem(item)
reaper.SetMediaItemInfo_Value(item, "D_POSITION", 0)
local only = os.getenv("NUBE_CASE")

for _, c in ipairs(CASES) do
  local name, src, params = c[1], c[2], c[3]
  if not only or name:find(only) then
    reaper.SetMediaTrackInfo_Value(tr, "I_NCHAN", c[4] or 2)
    local s = reaper.PCM_Source_CreateFromFile(ROOT .. "/signals/" .. src)
    reaper.SetMediaItemTake_Source(take, s)
    reaper.SetMediaItemInfo_Value(item, "D_LENGTH", (reaper.GetMediaSourceLength(s)))
    reaper.UpdateItemInProject(item)
    while reaper.TrackFX_GetCount(tr) > 0 do reaper.TrackFX_Delete(tr, 0) end
    local fx = reaper.TrackFX_AddByName(tr, "JS:Nube Comp/nube_comp.jsfx", false, -1)
    if fx < 0 then log("ERROR no cargó el FX") break end
    -- el preset primero (pisa todo), después lo demás
    if params[25] then reaper.TrackFX_SetParam(tr, fx, 24, params[25]) end
    for s_, v in pairs(params) do
      if s_ ~= 25 then
        if LOGP[s_] then reaper.TrackFX_SetParamNormalized(tr, fx, s_ - 1, to_norm(s_, v))
        else reaper.TrackFX_SetParam(tr, fx, s_ - 1, v) end
      end
    end
    local file = OUT .. "/" .. name .. ".wav"
    os.remove(file)
    reaper.GetSetProjectInfo(0, "RENDER_SETTINGS", 0, true)
    reaper.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", 1, true)
    reaper.GetSetProjectInfo(0, "RENDER_SRATE", 48000, true)
    reaper.GetSetProjectInfo(0, "RENDER_CHANNELS", 2, true)
    reaper.GetSetProjectInfo(0, "RENDER_TAILFLAG", 0, true)
    reaper.GetSetProjectInfo_String(0, "RENDER_FILE", OUT, true)
    reaper.GetSetProjectInfo_String(0, "RENDER_PATTERN", name, true)
    reaper.Main_OnCommand(42230, 0)
    local vals = {}
    for _, k in ipairs({1, 2, 3, 4, 5, 7, 8, 12, 13, 14}) do local _, v = reaper.TrackFX_GetFormattedParamValue(tr, fx, k - 1, ""); vals[#vals + 1] = v end
    log("caso", name, table.concat(vals, " | "))
  end
end
reaper.Main_SaveProjectEx(0, OUT .. "/_tmp_test.rpp", 0)
reaper.Main_openProject("noprompt:" .. OUT .. "/_tmp_test.rpp")
reaper.Main_OnCommand(40860, 0) -- cerrar pestaña
log("done")
logf:close()
