#!/usr/bin/env python3
"""Génère dashboard/index.html — dashboard à onglets (Portefeuille + Insight).
HTML autonome, données intégrées, aucune dépendance externe."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
portfolio = json.loads((ROOT / "dashboard" / "data.json").read_text())
insight = json.loads((ROOT / "dashboard" / "insight.json").read_text())

HTML = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Adoption Utilisateurs Locaux</title>
<style>
:root{
  --bg:#fbfbfa; --panel:#fff; --ink:#1c1c1a; --muted:#6b6b66; --line:#e6e5e1;
  --bar:#c9c7c0; --bar-strong:#8a8880; --chip:#f0efeb;
}
:root[data-theme="dark"]{
  --bg:#14140f; --panel:#1d1d18; --ink:#ececff; --muted:#a0a09a; --line:#33332c;
  --bar:#3d3d35; --bar-strong:#6f6f64; --chip:#26261f;
}
.header-row{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}
.theme-toggle{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:999px;
  padding:6px 12px;font:inherit;font-size:12.5px;cursor:pointer;white-space:nowrap;display:flex;align-items:center;gap:6px}
.theme-toggle:hover{border-color:var(--bar-strong)}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1280px;margin:0 auto;padding:24px 22px 60px}
h1{font-size:19px;margin:0 0 2px}
.sub{color:var(--muted);font-size:12.5px;margin-bottom:16px}
.tabs{display:flex;gap:4px;border-bottom:1px solid var(--line);margin-bottom:20px}
.tabs button{background:none;border:none;border-bottom:2px solid transparent;color:var(--muted);
  font:inherit;font-weight:600;padding:9px 14px;cursor:pointer}
.tabs button.on{color:var(--ink);border-color:var(--ink)}
.kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:14px}
@media(max-width:860px){.kpis{grid-template-columns:repeat(2,1fr)}}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:13px 14px}
.kpi .lab{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.kpi .val{font-size:22px;font-weight:600;margin-top:3px;font-variant-numeric:tabular-nums}
.kpi .rat{font-size:12px;color:var(--muted);margin-top:1px}
.note{background:var(--chip);border:1px solid var(--line);border-radius:8px;padding:9px 12px;font-size:12px;color:var(--muted);margin:14px 0 20px}
.section-h{font-size:15px;font-weight:700;margin:24px 0 12px;padding-bottom:7px;border-bottom:2px solid var(--line);letter-spacing:.02em}
.section-h:first-of-type{margin-top:4px}
details.panel{padding:0}
details.panel summary{cursor:pointer;list-style:none;padding:16px;font-size:13px;font-weight:600;display:flex;align-items:center;justify-content:space-between}
details.panel summary::-webkit-details-marker{display:none}
details.panel summary::after{content:'▾';color:var(--muted);font-size:11px}
details.panel[open] summary::after{content:'▴'}
details.panel>div{padding:0 16px 16px}
.vd-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
@media(max-width:860px){.vd-grid{grid-template-columns:repeat(2,1fr)}}
.kpi.vd .sub2{font-size:11px;color:var(--muted);margin-top:3px;white-space:normal}
.kpi.vd .dlt{font-size:12px;margin-top:5px;font-variant-numeric:tabular-nums}
.kpi.vd .dlt.up{color:#3a915f}
.kpi.vd .dlt.dn{color:#b5562f}
.kpi.vd .dlt.flat{color:var(--muted)}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px;margin-bottom:20px}
.panel h2{font-size:13px;margin:0 0 12px;font-weight:600}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media(max-width:900px){.grid2{grid-template-columns:1fr}}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin-top:8px}
.legend i{display:inline-block;width:10px;height:2px;vertical-align:middle;margin-right:5px}
.controls{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px;align-items:center}
.controls input,.controls select{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:7px;padding:7px 9px;font:inherit}
.controls select:disabled{opacity:.45;cursor:not-allowed}
.filterbar{display:flex;flex-wrap:wrap;align-items:center;gap:12px 16px;margin-bottom:8px}
.filterbar .f-primary{font-weight:600}
.filterbar .f-primary select{font-weight:600;padding:8px 10px}
.filterbar .f-secondary{display:flex;flex-wrap:wrap;gap:9px 14px;align-items:center;padding-left:16px;border-left:2px solid var(--line)}
.filterbar .f-secondary label{color:var(--muted)}
.filterbar .f-secondary select{max-width:220px}
.ms{position:relative;display:inline-block;font-weight:400}
.ms-btn{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:7px;padding:7px 9px;font:inherit;cursor:pointer;max-width:230px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:left}
.ms.has .ms-btn{border-color:var(--bar-strong)}
.ms.ms-off .ms-btn{opacity:.45;cursor:not-allowed}
.ms-pop{position:absolute;z-index:40;top:calc(100% + 4px);left:0;width:300px;max-width:80vw;background:var(--panel);border:1px solid var(--line);border-radius:9px;box-shadow:0 6px 24px rgba(0,0,0,.22);padding:8px}
.ms-q{width:100%;background:var(--bg);color:var(--ink);border:1px solid var(--line);border-radius:6px;padding:6px 8px;font:inherit;margin-bottom:6px}
.ms-list{max-height:280px;overflow:auto}
.ms-grp{font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin:8px 0 3px;padding-left:2px}
.ms-grp:first-child{margin-top:0}
.ms-it{display:flex;align-items:center;gap:7px;padding:4px 4px;border-radius:5px;font-size:13px;cursor:pointer}
.ms-it:hover{background:var(--chip)}
.ms-it input{margin:0}
.ms-empty{color:var(--muted);font-size:12px;padding:8px 2px}
.ms-act{border-top:1px solid var(--line);margin-top:6px;padding-top:6px;text-align:right}
.ms-act button{background:var(--chip);color:var(--ink);border:1px solid var(--line);border-radius:6px;padding:4px 9px;font:inherit;font-size:12px;cursor:pointer}
table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}
th,td{text-align:right;padding:7px 9px;border-bottom:1px solid var(--line);white-space:nowrap}
th:first-child,td:first-child{text-align:left}
th{font-size:11px;text-transform:uppercase;letter-spacing:.03em;color:var(--muted);cursor:pointer;user-select:none;position:sticky;top:0;background:var(--panel)}
th.sorted::after{content:" \25BE";font-size:9px}
th.asc.sorted::after{content:" \25B4"}
td.name{font-weight:500}
.chip{display:inline-block;font-size:11px;padding:1px 7px;border:1px solid var(--line);border-radius:999px;color:var(--muted)}
.cell{display:flex;flex-direction:column;align-items:flex-end;gap:3px}
.barbg{width:82px;height:4px;background:var(--bar);border-radius:2px;overflow:hidden}
.barfg{height:100%;background:var(--bar-strong)}
.muted{color:var(--muted)}
.tbl-scroll{overflow-x:auto;max-height:520px;overflow-y:auto}
.foot{font-size:11.5px;color:var(--muted);margin-top:10px}
ol.rank{margin:0;padding-left:20px;font-size:13px}
ol.rank li{margin:2px 0}
ol.rank .n{color:var(--muted);font-variant-numeric:tabular-nums}
.pcell,.acell{cursor:pointer;text-decoration:underline dotted;text-underline-offset:2px}
#i_tip{position:fixed;z-index:60;background:var(--ink);color:var(--bg);font-size:12px;line-height:1.45;
  padding:7px 10px;border-radius:6px;white-space:pre;pointer-events:none;max-width:300px;
  box-shadow:0 2px 12px rgba(0,0,0,.25)}
.modal-bg{position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:50;padding:20px}
.modal{background:var(--panel);border:1px solid var(--line);border-radius:12px;max-width:520px;width:100%;max-height:72vh;overflow:auto;padding:18px 20px}
.modal h3{margin:0 0 4px;font-size:14px}
.modal .sub2{color:var(--muted);font-size:12px;margin-bottom:10px}
.modal ul{margin:0;padding-left:18px;font-size:13px;columns:2}
@media(max-width:520px){.modal ul{columns:1}}
.modal button{margin-top:12px;background:var(--chip);border:1px solid var(--line);border-radius:7px;padding:6px 12px;font:inherit;color:var(--ink);cursor:pointer}
[hidden]{display:none!important}
</style>
<script>
(function(){
  try{ if(localStorage.getItem('theme') === 'dark') document.documentElement.setAttribute('data-theme','dark'); }
  catch(e){}
})();
</script>
</head>
<body>
<div class="wrap">
  <div class="header-row">
    <div>
      <h1>Adoption des utilisateurs locaux</h1>
      <div class="sub" id="sub"></div>
    </div>
    <button class="theme-toggle" id="theme_toggle" type="button"></button>
  </div>

  <div class="tabs">
    <button data-tab="portfolio" class="on">Vue Portefeuille</button>
    <button data-tab="insight">Module Insight</button>
    <button data-tab="erep">E-réputation</button>
    <button data-tab="inbox">Module Inbox</button>
  </div>

  <!-- ===================== PORTEFEUILLE ===================== -->
  <section id="tab-portfolio">
    <div class="kpis" id="p_kpis"></div>
    <div class="note" id="p_disclaimer"></div>
    <div class="panel">
      <h2>Activité quotidienne — utilisateurs distincts (90 jours)</h2>
      <div id="p_chart"></div>
      <div class="legend">
        <span><i style="background:#8a8880"></i>Connectés</span>
        <span><i style="background:#3a7bd5"></i>Inbox</span>
        <span><i style="background:#c77d3a"></i>E-réputation</span>
        <span><i style="background:#6cc79a"></i>Insight</span>
      </div>
    </div>
    <div class="panel">
      <h2>Comptes clients</h2>
      <div class="controls">
        <input id="p_q" placeholder="Rechercher un client…" style="min-width:200px">
        <select id="p_csm"><option value="">Tous les CSM</option></select>
        <select id="p_renew"><option value="">Tout renouvellement</option><option value="not risky">not risky</option><option value="risky">risky</option></select>
        <select id="p_insight"><option value="">Tous</option><option value="1">Éligibles Insight</option><option value="0">Non éligibles</option></select>
      </div>
      <div class="tbl-scroll"><table id="p_t"><thead><tr id="p_hrow"></tr></thead><tbody id="p_tb"></tbody></table></div>
      <div class="foot" id="p_tfoot"></div>
    </div>
  </section>

  <!-- ===================== INSIGHT ===================== -->
  <section id="tab-insight" hidden>
    <div class="controls filterbar">
      <label class="f-primary">Compte&nbsp;
        <select id="i_customer"></select>
      </label>
      <div class="f-secondary">
        <label>Période&nbsp;
          <select id="i_period">
            <option value="30d">30 derniers jours</option>
            <option value="prevmonth">Mois précédent</option>
            <option value="quarter">Trimestre actuel</option>
            <option value="year">Année courante</option>
            <option value="custom">Custom…</option>
          </select>
        </label>
        <label id="i_custom_wrap" hidden>du&nbsp;<input type="date" id="i_from">&nbsp;au&nbsp;<input type="date" id="i_to"></label>
        <label>Niveau&nbsp;
          <select id="i_gran">
            <option value="">Utilisateur</option>
            <option value="place">Place / point de vente</option>
            <option value="zone">Zone</option>
            <option value="sector">Secteur</option>
            <option value="subtype">Sous-type</option>
            <option value="region">Région</option>
            <option value="department">Département</option>
            <option value="country">Pays</option>
            <option value="type">Type</option>
            <option value="brand">Brand level</option>
          </select>
        </label>
        <label>Périmètre&nbsp;
          <span class="ms" id="i_unit_ms">
            <button type="button" class="ms-btn" id="i_unit_btn"><span id="i_unit_lbl">Tout le compte</span> ▾</button>
            <div class="ms-pop" id="i_unit_pop" hidden>
              <input type="text" class="ms-q" id="i_unit_q" placeholder="Rechercher une unité…" autocomplete="off">
              <div class="ms-list" id="i_unit_list"></div>
              <div class="ms-act"><button type="button" id="i_unit_clear">Tout effacer</button></div>
            </div>
          </span>
        </label>
        <span id="i_period_dates" class="muted"></span>
      </div>
    </div>
    <div class="controls" style="margin-top:-6px"><span class="muted" id="i_ctx"></span> <span class="muted" id="i_gran_hint"></span></div>
    <div class="note" id="i_disclaimer"></div>

    <h2 class="section-h">Adoption</h2>
    <div class="kpis" id="i_kpis" style="grid-template-columns:repeat(2,minmax(200px,260px))"></div>

    <div class="panel">
      <h2 id="i_chart_h">Utilisateurs actifs Insight — quotidien</h2>
      <div id="i_chart"></div>
      <div class="legend">
        <span><i style="background:#6cc79a"></i>Actifs Insight</span>
        <span><i style="background:#3a7bd5"></i>Quick Overview</span>
        <span><i style="background:#c77d3a"></i>Carte de synthèse</span>
      </div>
    </div>

    <div class="panel">
      <h2 id="i_feat_h">Actifs par fonctionnalité</h2>
      <div class="tbl-scroll"><table id="i_feat"><thead><tr>
        <th>Fonctionnalité</th><th>Utilisateurs actifs</th><th>% des actifs</th><th>Actions</th><th>Actions / utilisateur</th>
      </tr></thead><tbody id="i_feat_tb"></tbody></table></div>
    </div>

    <div class="grid2">
      <div class="panel">
        <h2 id="i_top_h">Top adopters (30 jours)</h2>
        <ol class="rank" id="i_top"></ol>
      </div>
      <div class="panel">
        <h2 id="i_drop_h">Adoption drop-off (30 jours)</h2>
        <ol class="rank" id="i_drop"></ol>
        <div class="foot" id="i_drop_foot"></div>
      </div>
    </div>

    <details class="panel" open>
      <summary><span id="i_rank_h2">Classement d'adoption (30 jours)</span></summary>
      <div>
        <div class="controls">
          <input id="i_q" placeholder="Rechercher un utilisateur…" style="min-width:220px">
          <label id="i_slider_wrap" class="muted">Places&nbsp;≤&nbsp;
            <input type="range" id="i_places" min="1" max="10" value="10" style="vertical-align:middle">
            <span id="i_places_val">10+</span>
          </label>
        </div>
        <div class="tbl-scroll"><table id="i_rank"><thead><tr id="i_rank_h"></tr></thead><tbody id="i_rank_tb"></tbody></table></div>
        <div class="foot" id="i_rank_foot"></div>
      </div>
    </details>
    <div id="i_modal" hidden></div>
    <div id="i_tip" hidden></div>

    <details class="panel">
      <summary>Ambassadeurs &amp; détracteurs par fonctionnalité (30 jours)</summary>
      <div id="i_ambass"></div>
    </details>

    <h2 class="section-h">Value Driver</h2>
    <div class="panel" id="i_vd_panel">
      <h2 id="i_vd_h">Value driver · Actionnabilité</h2>
      <div class="vd-grid" id="i_vd"></div>
      <div class="foot" id="i_vd_foot"></div>
    </div>
  </section>

  <!-- ===================== E-REPUTATION ===================== -->
  <section id="tab-erep" hidden>
    <div class="controls filterbar">
      <label class="f-primary">Compte&nbsp;
        <select id="e_customer"></select>
      </label>
      <div class="f-secondary">
        <label>Période&nbsp;
          <select id="e_period">
            <option value="30d">30 derniers jours</option>
            <option value="prevmonth">Mois précédent</option>
            <option value="quarter">Trimestre actuel</option>
            <option value="year">Année courante</option>
            <option value="custom">Custom…</option>
          </select>
        </label>
        <label id="e_custom_wrap" hidden>du&nbsp;<input type="date" id="e_from">&nbsp;au&nbsp;<input type="date" id="e_to"></label>
        <label>Niveau&nbsp;
          <select id="e_gran">
            <option value="">Utilisateur</option>
            <option value="place">Place / point de vente</option>
            <option value="zone">Zone</option>
            <option value="sector">Secteur</option>
            <option value="subtype">Sous-type</option>
            <option value="region">Région</option>
            <option value="department">Département</option>
            <option value="country">Pays</option>
            <option value="type">Type</option>
            <option value="brand">Brand level</option>
          </select>
        </label>
        <label>Périmètre&nbsp;
          <span class="ms" id="e_unit_ms">
            <button type="button" class="ms-btn" id="e_unit_btn"><span id="e_unit_lbl">Tout le compte</span> ▾</button>
            <div class="ms-pop" id="e_unit_pop" hidden>
              <input type="text" class="ms-q" id="e_unit_q" placeholder="Rechercher une unité…" autocomplete="off">
              <div class="ms-list" id="e_unit_list"></div>
              <div class="ms-act"><button type="button" id="e_unit_clear">Tout effacer</button></div>
            </div>
          </span>
        </label>
        <span id="e_period_dates" class="muted"></span>
      </div>
    </div>
    <div class="controls" style="margin-top:-6px"><span class="muted" id="e_ctx"></span> <span class="muted" id="e_gran_hint"></span></div>
    <div class="note" id="e_disclaimer"></div>

    <h2 class="section-h">Adoption</h2>
    <div class="kpis" id="e_kpis" style="grid-template-columns:repeat(2,minmax(200px,260px))"></div>

    <div class="panel">
      <h2 id="e_chart_h">Utilisateurs actifs Insight — quotidien</h2>
      <div id="e_chart"></div>
      <div class="legend">
        <span><i style="background:#6cc79a"></i>Actifs E-rép</span>
        <span><i style="background:#3a7bd5"></i>Note Google</span>
        <span><i style="background:#c77d3a"></i>Benchmark concurrentiel</span>
      </div>
    </div>

    <div class="panel">
      <h2 id="e_feat_h">Actifs par fonctionnalité</h2>
      <div class="tbl-scroll"><table id="e_feat"><thead><tr>
        <th>Fonctionnalité</th><th>Utilisateurs actifs</th><th>% des actifs</th><th>Actions</th><th>Actions / utilisateur</th><th>Adoption (accès)</th>
      </tr></thead><tbody id="e_feat_tb"></tbody></table></div>
    </div>

    <div class="grid2">
      <div class="panel">
        <h2 id="e_top_h">Top adopters (30 jours)</h2>
        <ol class="rank" id="e_top"></ol>
      </div>
      <div class="panel">
        <h2 id="e_drop_h">Adoption drop-off (30 jours)</h2>
        <ol class="rank" id="e_drop"></ol>
        <div class="foot" id="e_drop_foot"></div>
      </div>
    </div>

    <details class="panel" open>
      <summary><span id="e_rank_h2">Classement d'adoption (30 jours)</span></summary>
      <div>
        <div class="controls">
          <input id="e_q" placeholder="Rechercher un utilisateur…" style="min-width:220px">
          <label id="e_slider_wrap" class="muted">Places&nbsp;≤&nbsp;
            <input type="range" id="e_places" min="1" max="10" value="10" style="vertical-align:middle">
            <span id="e_places_val">10+</span>
          </label>
        </div>
        <div class="tbl-scroll"><table id="e_rank"><thead><tr id="e_rank_h"></tr></thead><tbody id="e_rank_tb"></tbody></table></div>
        <div class="foot" id="e_rank_foot"></div>
      </div>
    </details>
    <div id="e_modal" hidden></div>
    <div id="e_tip" hidden></div>

    <details class="panel">
      <summary>Ambassadeurs &amp; détracteurs par fonctionnalité (30 jours)</summary>
      <div id="e_ambass"></div>
    </details>

    <h2 class="section-h">Value Driver</h2>
    <div class="panel" id="e_vd_panel">
      <h2 id="e_vd_h">Value driver · Acquisition</h2>
      <div class="vd-grid" id="e_vd"></div>
      <div class="foot" id="e_vd_foot"></div>
    </div>

    <div class="grid2">
      <div class="panel">
        <h2 id="e_topflop_h">Top / flop établissements — Note Google</h2>
        <div class="grid2">
          <div><div class="muted" style="font-size:11px;text-transform:uppercase;margin-bottom:4px">Top</div>
            <ol class="rank" id="e_gtop"></ol></div>
          <div><div class="muted" style="font-size:11px;text-transform:uppercase;margin-bottom:4px">Flop</div>
            <ol class="rank" id="e_gflop"></ol></div>
        </div>
        <div class="foot" id="e_gtopflop_foot"></div>
      </div>
    </div>
  </section>

  <!-- ===================== INBOX ===================== -->
  <section id="tab-inbox" hidden>
    <div class="controls filterbar">
      <label class="f-primary">Compte&nbsp;
        <select id="x_customer"></select>
      </label>
      <div class="f-secondary">
        <label>Niveau&nbsp;
          <select id="x_gran">
            <option value="">Utilisateur</option>
            <option value="place">Place / point de vente</option>
            <option value="zone">Zone</option>
            <option value="sector">Secteur</option>
            <option value="subtype">Sous-type</option>
            <option value="region">Région</option>
            <option value="department">Département</option>
            <option value="country">Pays</option>
            <option value="type">Type</option>
            <option value="brand">Brand level</option>
          </select>
        </label>
        <label>Périmètre&nbsp;
          <span class="ms" id="x_unit_ms">
            <button type="button" class="ms-btn" id="x_unit_btn"><span id="x_unit_lbl">Tout le compte</span> ▾</button>
            <div class="ms-pop" id="x_unit_pop" hidden>
              <input type="text" class="ms-q" id="x_unit_q" placeholder="Rechercher une unité…" autocomplete="off">
              <div class="ms-list" id="x_unit_list"></div>
              <div class="ms-act"><button type="button" id="x_unit_clear">Tout effacer</button></div>
            </div>
          </span>
        </label>
      </div>
    </div>
    <div class="controls" style="margin-top:-6px"><span class="muted" id="x_ctx"></span> <span class="muted" id="x_gran_hint"></span></div>
    <div class="note" id="x_disclaimer"></div>

    <h2 class="section-h">Adoption <span class="chip">fenêtre fixe 30 jours</span></h2>
    <div class="kpis" id="x_kpis" style="grid-template-columns:repeat(3,minmax(200px,260px))"></div>

    <div class="panel">
      <h2 id="x_chart_h">Connectés &amp; actifs Inbox — quotidien</h2>
      <div class="controls" style="margin-top:-4px">
        <label class="muted">Période de la courbe&nbsp;
          <select id="x_period">
            <option value="30d">30 derniers jours</option>
            <option value="prevmonth">Mois précédent</option>
            <option value="quarter">Trimestre actuel</option>
            <option value="year">Année courante</option>
            <option value="custom">Custom…</option>
          </select>
        </label>
        <label id="x_custom_wrap" hidden>du&nbsp;<input type="date" id="x_from">&nbsp;au&nbsp;<input type="date" id="x_to"></label>
        <span id="x_period_dates" class="muted"></span>
      </div>
      <div id="x_chart"></div>
      <div class="legend">
        <span><i style="background:#6cc79a"></i>Connectés Inbox</span>
        <span><i style="background:#3a7bd5"></i>Actifs Inbox</span>
      </div>
      <div class="foot">Seule cette courbe suit le sélecteur de période ci-dessus ; elle reste à la maille compte (non filtrable par périmètre). Le reste de l'onglet (KPI, top/drop, classement, value driver) reste sur une fenêtre fixe de 30 jours.</div>
    </div>

    <div class="grid2">
      <div class="panel">
        <h2 id="x_top_h">Top adopters (30 jours)</h2>
        <ol class="rank" id="x_top"></ol>
      </div>
      <div class="panel">
        <h2 id="x_drop_h">Adoption drop-off (30 jours)</h2>
        <ol class="rank" id="x_drop"></ol>
        <div class="foot" id="x_drop_foot"></div>
      </div>
    </div>

    <details class="panel" open>
      <summary><span id="x_rank_h2">Classement d'adoption (30 jours)</span></summary>
      <div>
        <div class="controls">
          <input id="x_q" placeholder="Rechercher un utilisateur…" style="min-width:220px">
          <label id="x_slider_wrap" class="muted">Places&nbsp;≤&nbsp;
            <input type="range" id="x_places" min="1" max="10" value="10" style="vertical-align:middle">
            <span id="x_places_val">10+</span>
          </label>
        </div>
        <div class="tbl-scroll"><table id="x_rank"><thead><tr id="x_rank_h"></tr></thead><tbody id="x_rank_tb"></tbody></table></div>
        <div class="foot" id="x_rank_foot"></div>
      </div>
    </details>
    <div id="x_modal" hidden></div>
    <div id="x_tip" hidden></div>

    <h2 class="section-h">Value Driver</h2>
    <div class="panel" id="x_vd_panel">
      <h2 id="x_vd_h">Value driver · Culture Client</h2>
      <div class="vd-grid" id="x_vd"></div>
      <div class="foot" id="x_vd_foot"></div>
    </div>
  </section>
</div>

<script src="data.js"></script>
<script>
const PORTFOLIO = window.__PORTFOLIO__ || {};
const INSIGHT = window.__INSIGHT__ || {};
if(!window.__PORTFOLIO__){
  document.body.innerHTML = '<div style="padding:40px;font:14px system-ui;color:#e5484d">'
    + 'data.js introuvable. Ouvre le dashboard via un petit serveur local :<br><br>'
    + '<code>cd "'+""+'dossier du dashboard'+'" &amp;&amp; python3 -m http.server 8000</code>'
    + '<br>puis http://localhost:8000/index.html</div>';
  throw new Error('data.js missing');
}
const nf = new Intl.NumberFormat('fr-FR');
const pct = x => (x*100).toFixed(1).replace('.',',') + ' %';
const r2 = x => (Math.round(x*100)/100).toString().replace('.',',');

/* ---------- thème clair/sombre ---------- */
// Défaut : clair. Le choix (s'il diffère du défaut) est mémorisé en localStorage
// et réappliqué au chargement via le petit script inline dans <head> (anti-flash).
(function(){
  const btn = document.getElementById('theme_toggle');
  function label(){
    const dark = document.documentElement.getAttribute('data-theme') === 'dark';
    btn.textContent = dark ? '☀️ Mode clair' : '🌙 Mode sombre';
  }
  btn.onclick = () => {
    const dark = document.documentElement.getAttribute('data-theme') === 'dark';
    if(dark){ document.documentElement.removeAttribute('data-theme'); }
    else{ document.documentElement.setAttribute('data-theme','dark'); }
    try{ localStorage.setItem('theme', dark ? 'light' : 'dark'); }catch(e){}
    label();
  };
  label();
})();

/* ---------- filtres partagés entre onglets (Insight / E-rép / Inbox) ---------- */
// Sélectionner un compte/période/niveau/périmètre sur un onglet le reporte sur les
// autres (quand compatible). Chaque module s'enregistre via registerFilterSync() une
// fois initialisé ; syncFilters() re-applique l'état partagé à tous les autres modules.
const SHARED_FILTERS = { customer: '', period: '30d', from: '', to: '', gran: '', perim: [] };
const FILTER_APPLIERS = {};
function registerFilterSync(key, applyFn){ FILTER_APPLIERS[key] = applyFn; }
function syncFilters(fromKey, patch){
  Object.assign(SHARED_FILTERS, patch);
  for(const k in FILTER_APPLIERS){
    if(k === fromKey) continue;
    try{ FILTER_APPLIERS[k](SHARED_FILTERS); }catch(e){ /* onglet pas encore prêt */ }
  }
}

/* ---------- tabs ---------- */
let EREP_LOADED = false, INBOX_LOADED = false;
document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('.tabs button').forEach(x=>x.classList.toggle('on',x===b));
  document.querySelectorAll('section[id^=tab-]').forEach(s=> s.hidden = s.id !== 'tab-'+b.dataset.tab);
  if(b.dataset.tab==='erep' && !EREP_LOADED){
    EREP_LOADED = true;
    document.getElementById('e_kpis').innerHTML = '<div class="muted" style="padding:20px">Chargement des données E-réputation…</div>';
    const sc = document.createElement('script'); sc.src = 'erep.js';
    sc.onload = ()=>{ try{ initErep(); }catch(err){ document.getElementById('e_kpis').innerHTML='<div style="color:#e5484d;padding:20px">Erreur E-rép : '+err.message+'</div>'; } };
    sc.onerror = ()=>{ document.getElementById('e_kpis').innerHTML='<div style="color:#e5484d;padding:20px">erep.js introuvable (même dossier, via serveur local).</div>'; };
    document.body.appendChild(sc);
  }
  if(b.dataset.tab==='inbox' && !INBOX_LOADED){
    INBOX_LOADED = true;
    document.getElementById('x_kpis').innerHTML = '<div class="muted" style="padding:20px">Chargement des données Inbox…</div>';
    const sc = document.createElement('script'); sc.src = 'inbox.js';
    sc.onload = ()=>{ try{ initInbox(); }catch(err){ document.getElementById('x_kpis').innerHTML='<div style="color:#e5484d;padding:20px">Erreur Inbox : '+err.message+'</div>'; } };
    sc.onerror = ()=>{ document.getElementById('x_kpis').innerHTML='<div style="color:#e5484d;padding:20px">inbox.js introuvable (même dossier, via serveur local).</div>'; };
    document.body.appendChild(sc);
  }
});

/* ======================================================= PORTEFEUILLE */
(function(){
  const T = PORTFOLIO.totals;
  document.getElementById('sub').textContent =
    `Fenêtre glissante 30 j · données extraites le ${PORTFOLIO.generated_at}`;
  const kpis = [
    ['Créés', T.created_users, null],
    ['Connectés', T.connected_users, T.connected_users/T.created_users],
    ['Actifs Inbox', T.active_inbox, T.active_inbox/T.connected_users],
    ['Actifs E-réputation', T.active_ereput, T.active_ereput/T.connected_users],
    ['Actifs Insight', T.active_insight, T.active_insight/T.connected_users],
  ];
  document.getElementById('p_kpis').innerHTML = kpis.map(([l,v,r],idx)=>`
    <div class="kpi"><div class="lab">${l}</div><div class="val">${nf.format(v)}</div>
    <div class="rat">${r!=null? pct(r)+(idx===1?' des créés':' des connectés'):'&nbsp;'}</div></div>`).join('')
    + `<div class="kpi" style="grid-column:1/-1"><div class="lab">Réponses Inbox envoyées (30 j)</div>
       <div class="val">${nf.format(T.inbox_replies)}</div>
       <div class="rat">${pct(T.inbox_replies_ai/T.inbox_replies)} via IA</div></div>`;
  document.getElementById('p_disclaimer').textContent =
    "V1 descriptive. Les chiffres « actifs » de cet écran sont exactement ceux des onglets de chaque module "
    + "(même définition, même source) : Inbox = a envoyé au moins une réponse, E-réputation = a consulté la note "
    + "Google ou le benchmark, Insight = a utilisé l'une des 3 features (comptes éligibles Insight uniquement). "
    + "Agrégats à la maille compte ; l'attribution par établissement (utilisateurs multi-sites) est traitée dans "
    + "les écrans de détail.";

  lineChart('p_chart', PORTFOLIO.trend.slice(0,-1),
    [['connected','#8a8880','Connectés'],['inbox','#3a7bd5','Inbox'],['ereput','#c77d3a','E-réputation'],['insight','#6cc79a','Insight']], 'd');

  const COLS = [
    {k:'customer_name',t:'Client',kind:'name'},
    {k:'csm_owner',t:'CSM',kind:'text'},
    {k:'renewal_status',t:'Renouv.',kind:'chip'},
    {k:'created_users',t:'Créés',kind:'num'},
    {k:'ratio_connected_created',t:'Connectés / créés',kind:'ratio',cnt:'connected_users'},
    {k:'ratio_inbox',t:'Inbox / connectés',kind:'ratio',cnt:'active_inbox'},
    {k:'ratio_ereput',t:'E-rép / connectés',kind:'ratio',cnt:'active_ereput'},
    {k:'ratio_insight',t:'Insight / connectés',kind:'ratio',cnt:'active_insight',elig:true},
    {k:'inbox_replies',t:'Rép. Inbox (% IA)',kind:'replies'},
  ];
  let sortK='created_users',sortAsc=false;
  const P = PORTFOLIO.portfolio.map(r=>({...r,
    ratio_connected_created:+r.ratio_connected_created,ratio_inbox:+r.ratio_inbox,
    ratio_ereput:+r.ratio_ereput,ratio_insight:+r.ratio_insight,ratio_replies_ai:+r.ratio_replies_ai}));
  const csmSel=document.getElementById('p_csm');
  [...new Set(P.map(r=>r.csm_owner).filter(Boolean))].sort().forEach(c=>csmSel.add(new Option(c,c)));
  document.getElementById('p_hrow').innerHTML = COLS.map(c=>`<th data-k="${c.k}">${c.t}</th>`).join('');
  document.querySelectorAll('#p_hrow th').forEach(th=>th.onclick=()=>{
    const k=th.dataset.k; sortAsc=(k===sortK)?!sortAsc:false; sortK=k; draw();
  });
  ['p_q','p_csm','p_renew','p_insight'].forEach(id=>document.getElementById(id).oninput=draw);
  function draw(){
    const q=p_q.value.toLowerCase(),fc=p_csm.value,fr=p_renew.value,fi=p_insight.value;
    let rows=P.filter(r=>(!q||(r.customer_name||'').toLowerCase().includes(q))
      &&(!fc||r.csm_owner===fc)&&(!fr||r.renewal_status===fr)
      &&(fi===''||String(r.is_insight_eligible?1:0)===fi));
    rows.sort((a,b)=>{let x=a[sortK],y=b[sortK];
      if(typeof x==='string'||typeof y==='string'){x=(x||'')+'';y=(y||'')+'';return sortAsc?x.localeCompare(y):y.localeCompare(x);}
      return sortAsc?x-y:y-x;});
    document.getElementById('p_tb').innerHTML=rows.map(r=>'<tr>'+COLS.map(c=>{
      if(c.kind==='name')return`<td class="name">${r.customer_name||'—'}</td>`;
      if(c.kind==='text')return`<td style="text-align:left" class="muted">${r[c.k]||'—'}</td>`;
      if(c.kind==='chip')return`<td style="text-align:left"><span class="chip">${r[c.k]||'—'}</span></td>`;
      if(c.kind==='num')return`<td>${nf.format(r[c.k])}</td>`;
      if(c.kind==='replies')return`<td><div class="cell"><span>${nf.format(r.inbox_replies)}</span>`
        +`<span class="muted" style="font-size:11px">${r.inbox_replies?pct(r.ratio_replies_ai)+' IA':'—'}</span></div></td>`;
      if(c.kind==='ratio'){
        if(c.elig&&!r.is_insight_eligible)return`<td class="muted">—</td>`;
        const v=r[c.k]||0,w=Math.max(0,Math.min(1,v))*100;
        return`<td><div class="cell"><span>${pct(v)} <span class="muted" style="font-size:11px">(${nf.format(r[c.cnt])})</span></span>`
          +`<span class="barbg"><span class="barfg" style="width:${w.toFixed(0)}%"></span></span></div></td>`;}
    }).join('')+'</tr>').join('');
    document.querySelectorAll('#p_hrow th').forEach(th=>{
      th.classList.toggle('sorted',th.dataset.k===sortK);th.classList.toggle('asc',th.dataset.k===sortK&&sortAsc);});
    document.getElementById('p_tfoot').textContent=`${rows.length} compte(s) sur ${P.length}`;
  }
  draw();
})();

/* ======================================================= INSIGHT */
(function(){
  const FEATURES = [
    {key:'overview',  label:'Quick Overview'},
    {key:'synthesis', label:'Carte de synthèse'},
    {key:'thematic',  label:'Page thématique'},
  ];
  const custs = INSIGHT.customers.slice().sort((a,b)=>b.connected_users-a.connected_users);
  const UNITS = INSIGHT.units || [];
  const USER_UNITS = INSIGHT.user_units || {};
  const PERIMETERS = INSIGHT.perimeters || [];
  // dénominateurs "connectés" par période — index : 0=30j, 1=mois préc., 2=trimestre, 3=année
  const CONN_PERIOD = INSIGHT.connected_period || {};
  const CONN_PERIOD_UNIT = (() => {
    const m = new Map();
    for(const r of (INSIGHT.connected_period_unit || [])) m.set(r[0] + '|' + r[1], [r[2], r[3], r[4], r[5]]);
    return m;
  })();
  const PERIOD_IDX = {'30d':0, 'prevmonth':1, 'quarter':2, 'year':3};
  // Insight/E-rép : les actifs sont recalculés côté client sur la période choisie,
  // le dénominateur doit donc suivre. Période "custom" -> undefined -> ratio masqué.
  function connIdx(){ return PERIOD_IDX[perSel.value]; }
  const DU = INSIGHT.daily_user || [];
  const UDIM = INSIGHT.user_dim || {};
  const USER_PLACES = INSIGHT.user_places || {};
  const SAL_IDX = {place:0,zone:1,sector:2,subtype:3,region:4,department:5,country:6,type:7,brand:8};
  const DATA_MAX = INSIGHT.data_max || new Date().toISOString().slice(0,10);
  const DATA_MIN = INSIGHT.data_min || DATA_MAX;
  const LEVEL_LABELS = {place:'places',zone:'zones',sector:'secteurs',subtype:'sous-types',
    region:'régions',department:'départements',country:'pays',type:'types',brand:'brand levels'};
  const LEVEL_SING = {place:'Place',zone:'Zone',sector:'Secteur',subtype:'Sous-type',
    region:'Région',department:'Département',country:'Pays',type:'Type',brand:'Brand level'};
  const PLABELS = {'30d':'30 derniers jours','prevmonth':'mois précédent','quarter':'trimestre actuel',
    'year':'année courante','custom':'période custom'};
  const MS = '(accès multi-strates)';

  const sel = document.getElementById('i_customer');
  const gsel = document.getElementById('i_gran');
  const usel = makePerim('i', () => { syncFilters('insight', {perim: usel.values}); render(); }, LEVEL_SING);
  const perSel = document.getElementById('i_period');
  const fromEl = document.getElementById('i_from'), toEl = document.getElementById('i_to');
  const slider = document.getElementById('i_places');
  const sliderWrap = document.getElementById('i_slider_wrap');
  const tipEl = document.getElementById('i_tip');

  sel.add(new Option(`Tous les comptes éligibles (${custs.length})`, ''));
  custs.slice().sort((a,b)=>a.customer_name.localeCompare(b.customer_name)).forEach(c=>sel.add(new Option(`${c.customer_name} — ${nf.format(c.active_insight_users)} actifs (30 j)`, c.customer_id)));
  fromEl.min = toEl.min = DATA_MIN; fromEl.max = toEl.max = DATA_MAX;
  fromEl.value = DATA_MIN; toEl.value = DATA_MAX;

  sel.onchange = () => { syncFilters('insight', {customer: sel.value, perim: [], gran: ''}); render(); };
  gsel.onchange = () => { syncFilters('insight', {gran: gsel.value}); render(); };
  perSel.onchange = ()=>{ document.getElementById('i_custom_wrap').hidden = perSel.value!=='custom'; syncFilters('insight', {period: perSel.value}); render(); };
  fromEl.oninput = toEl.oninput = ()=>{ syncFilters('insight', {from: fromEl.value, to: toEl.value}); render(); };
  document.getElementById('i_q').oninput = renderRank;
  slider.oninput = ()=>{ document.getElementById('i_places_val').textContent = slider.value==='10'?'10+':slider.value; renderRank(); };

  document.getElementById('i_disclaimer').textContent =
    "Périmètre = comptes avec un semantic scheme configuré dont le nom ne commence pas par « - », et utilisateurs "
    + "du périmètre commun. Signaux : Quick Overview = table Topic Overview Consultations ; "
    + "Carte de synthèse = activité « Topic drill-down · overview » ; Page thématique = activités « Metric · SENTIMENT / SENTIMENT_OVERVIEW / Topic drill-down · thematic ». "
    + "« Actif Insight » = actif sur ≥ 1 des 3 fonctionnalités ou page vue monitored. "
    + "Le filtre de période s'applique à tout l'onglet (KPI, courbe, usage, top/drop, classement). "
    + "Le dénominateur « connectés » (tous modules) reste sur 30 jours, quelle que soit la période. "
    + "Granularité réglable quand un compte est sélectionné : rattachement hiérarchique (comme le filtre Périmètre) — un utilisateur compte dans une unité s'il l'administre directement OU si l'un de ses magasins administrés en dépend (entre 1 et 60 magasins administrés ; au-delà, profil siège/national exclu du classement par niveau). Un utilisateur peut appartenir à plusieurs unités du même niveau (ex. administre 2 régions) — la somme des « Connectés » sur toutes les lignes d'un niveau peut donc dépasser le total du compte — en général de quelques pourcents, mais jusqu'à +50 % sur les comptes très maillés (mesuré : Unibail au niveau Pays, 191 contre 126). Comparez donc les unités entre elles plutôt que de sommer les lignes. "
    + "Top adopters masque les unités à 0 action ; le classement les conserve.";

  let sortK='insight_actions', sortAsc=false;
  let USER_ROWS=[], renderedRows=[], renderedIsUnit=false;
  let PERIOD=['',''], PLBL='', IS_DEFAULT=true;

  /* ---------- période ---------- */
  function periodRange(){
    const iso = dt => dt.toISOString().slice(0,10);
    const emax = new Date(DATA_MAX + 'T00:00:00Z');
    const p = perSel.value;
    if(p === 'custom') return [fromEl.value || DATA_MIN, toEl.value || DATA_MAX];
    if(p === 'prevmonth'){
      const y=emax.getUTCFullYear(), m=emax.getUTCMonth();
      return [iso(new Date(Date.UTC(y, m-1, 1))), iso(new Date(Date.UTC(y, m, 0)))];
    }
    if(p === 'quarter'){
      const y=emax.getUTCFullYear(), q=Math.floor(emax.getUTCMonth()/3);
      return [iso(new Date(Date.UTC(y, q*3, 1))), DATA_MAX];
    }
    if(p === 'year') return [iso(new Date(Date.UTC(emax.getUTCFullYear(), 0, 1))), DATA_MAX];
    const s = new Date(emax); s.setUTCDate(s.getUTCDate() - 29);   // 30 j glissants inclus
    return [iso(s), DATA_MAX];
  }

  function periodUserRows(start, end, cid){
    const acc = new Map();
    for(const r of DU){
      if(r.d < start || r.d > end) continue;
      if(cid && r.k.split('|')[1] !== cid) continue;
      let o = acc.get(r.k);
      if(!o){ o = {ov:0,sy:0,th:0,mv:0,days:0}; acc.set(r.k, o); }
      o.ov+=r.ov||0; o.sy+=r.sy||0; o.th+=r.th||0; o.mv+=r.mv||0;
      if((r.ov||0)+(r.sy||0)+(r.th||0)+(r.mv||0) > 0) o.days += 1;
    }
    const out = [];
    for(const [key, a] of acc){
      const [username, customer_id] = key.split('|');
      const d = UDIM[key] || {};
      out.push({key, username, customer_id, customer_name: d.cn || '—', role: d.role || '',
        n_admin_places: d.np || 0, sal: d.sal || [],
        overview: a.ov, synthesis: a.sy, thematic: a.th, monitored_views: a.mv,
        active_days: a.days,
        insight_actions: a.ov + a.sy + a.th});
    }
    return out;
  }

  function periodDaily(start, end, cid, keySet){
    const byDay = new Map();
    for(const r of DU){
      if(r.d < start || r.d > end) continue;
      if(cid && r.k.split('|')[1] !== cid) continue;
      if(keySet && !keySet.has(r.k)) continue;
      let o = byDay.get(r.d);
      if(!o){ o = {d:r.d, act:new Set(), ov:new Set(), sy:new Set()}; byDay.set(r.d, o); }
      if((r.ov||0)+(r.sy||0)+(r.th||0)+(r.mv||0) > 0) o.act.add(r.k);
      if(r.ov > 0) o.ov.add(r.k);
      if(r.sy > 0) o.sy.add(r.k);
    }
    return [...byDay.values()].sort((a,b)=> a.d < b.d ? -1 : 1)
      .map(o=>({d:o.d, active_users:o.act.size, overview_users:o.ov.size, synthesis_users:o.sy.size}));
  }

  function connFor(cid){
    // Le dénominateur suit la période choisie (corrigé 2026-09-17) : auparavant il
    // restait figé à 30 j pendant que le numérateur "actifs" suivait la période,
    // ce qui gonflait le ratio (et le faisait dépasser 100 % sur certains comptes).
    // Période "custom" : non précalculable -> null, le ratio est alors masqué.
    const pi = connIdx();
    if(pi === undefined) return null;
    const cs = cid ? custs.filter(c=>c.customer_id===cid) : custs;
    return cs.reduce((s,c)=>{
      const a = CONN_PERIOD[c.customer_id];
      return s + (a ? (a[pi] || 0) : 0);
    }, 0);
  }
  function connForUnits(cid, tokens){
    const pi = connIdx();
    if(pi === undefined) return null;
    let s = 0;
    for(const t of tokens){
      const a = CONN_PERIOD_UNIT.get(cid + '|' + t);
      if(a) s += a[pi] || 0;
    }
    return s;
  }
  function ctxLabel(cid){
    const cs = cid ? custs.filter(c=>c.customer_id===cid) : custs;
    return cid ? (cs[0] ? cs[0].customer_name : '—') : `${cs.length} comptes`;
  }
  function rosterFor(cid){
    const cs = cid ? custs.filter(c=>c.customer_id===cid) : custs;
    return cs.reduce((s,c)=>s+(c.roster||0), 0);
  }

  function unitsForLevel(u, gran){
    // rattachement hiérarchique (option B, comme le Périmètre) — un utilisateur
    // peut appartenir à plusieurs unités du même niveau (ex. admin de 2 régions).
    const toks = USER_UNITS[u.key];
    if(!toks || !toks.length) return [];
    const out = [];
    for(const t of toks){
      const sep = t.indexOf('\u0001');
      if(t.slice(0, sep) === gran) out.push(t.slice(sep + 1));
    }
    return out;
  }
  function periodUnitRows(cid, gran){
    const byUnit = new Map();
    for(const u of USER_ROWS){
      const names = unitsForLevel(u, gran);
      for(const name of names){
        let o = byUnit.get(name);
        if(!o){ o = {ai:0,ia:0,ov:0,sy:0,th:0}; byUnit.set(name, o); }
        if(u.insight_actions + u.monitored_views > 0) o.ai += 1;
        o.ia += u.insight_actions; o.ov += u.overview; o.sy += u.synthesis; o.th += u.thematic;
      }
    }
    const pi = connIdx();
    return UNITS.filter(x=>x.customer_id===cid && x.level===gran).map(x=>{
      const p = byUnit.get(x.unit_name) || {ai:0,ia:0,ov:0,sy:0,th:0};
      // dénominateur par unité aligné sur la période sélectionnée (2026-09-17)
      const cp = pi===undefined ? null : CONN_PERIOD_UNIT.get(cid + '|' + gran + '\u0001' + x.unit_name);
      const conn = pi===undefined ? null : (cp ? (cp[pi] || 0) : 0);
      return {unit_name:x.unit_name, place_count:x.place_count, place_names:x.place_names,
        connected_users:conn,
        active_insight_users:p.ai, insight_actions:p.ia,
        overview_actions:p.ov, synthesis_actions:p.sy, thematic_actions:p.th,
        rate: conn ? p.ai / conn : 0};
    });
  }

  /* ---------- render principal ---------- */
  function render(){
    const cid = sel.value;
    if(usel.dataset.cid !== (cid||'')) usel.populate(cid, PERIMETERS);
    usel.disabled = !cid;
    PERIOD = periodRange();
    IS_DEFAULT = perSel.value === '30d';
    PLBL = PLABELS[perSel.value];
    document.getElementById('i_custom_wrap').hidden = perSel.value !== 'custom';
    document.getElementById('i_period_dates').textContent = IS_DEFAULT
      ? 'fenêtre glissante' : `${PERIOD[0]} → ${PERIOD[1]}`;
    const pTag = IS_DEFAULT ? '30 jours' : PLBL;
    document.getElementById('i_chart_h').textContent = `Utilisateurs actifs Insight — quotidien · ${pTag}`;
    document.getElementById('i_feat_h').textContent = `Actifs par fonctionnalité · ${pTag}`;

    USER_ROWS = periodUserRows(PERIOD[0], PERIOD[1], cid);
    const perimSel = cid ? usel.values : [];
    let unitScope = null;
    if(perimSel.length){
      const pset = new Set(perimSel);
      USER_ROWS = USER_ROWS.filter(u => (USER_UNITS[u.key]||[]).some(t=>pset.has(t)));
      const prows = PERIMETERS.filter(p=>p.customer_id===cid && pset.has(p.level+'\u0001'+p.unit_name));
      unitScope = { rows: prows, label: perimSel.length===1
        ? LEVEL_SING[perimSel[0].split('\u0001')[0]] + ' « ' + perimSel[0].split('\u0001')[1] + ' »'
        : perimSel.length + ' unités' };
    }
    const scopeP = unitScope ? {
      connected_users: connForUnits(cid, perimSel),
      connected_score_access: unitScope.rows.reduce((s,p)=>s+(p.connected_score_access||0),0),
      connected_bench_access: unitScope.rows.reduce((s,p)=>s+(p.connected_bench_access||0),0),
    } : null;
    const scopeKeys = unitScope ? new Set(USER_ROWS.map(u=>u.key)) : null;
    const active = USER_ROWS.length;
    const connected = scopeP ? scopeP.connected_users : connFor(cid);
    // Le dénominateur suit désormais la période (2026-09-17). Seule la période
    // "custom" n'est pas précalculable : connected vaut null et le ratio est masqué
    // plutôt que d'afficher un pourcentage faux.
    const jSuffix = IS_DEFAULT ? '' : ' (période)';
    const featCount = k => USER_ROWS.reduce((s,u)=> s + (u[k] > 0 ? 1 : 0), 0);
    const featActions = k => USER_ROWS.reduce((s,u)=> s + (u[k] || 0), 0);

    document.getElementById('i_ctx').textContent =
      (cid ? `${ctxLabel(cid)} · ${nf.format(rosterFor(cid))} comptes créés · ` : `${ctxLabel(cid)} · `)
      + `${connected==null ? '—' : nf.format(connected)} connectés${jSuffix} · période : ${IS_DEFAULT ? '30 j' : PERIOD[0]+' → '+PERIOD[1]}`
      + (unitScope ? ` · périmètre : ${unitScope.label}` + (perimSel.length>1 ? ' (connectés = somme des unités)' : '') : '');

    const kpis = [
      ['Connectés', connected, null, connected==null ? 'non calculable sur période personnalisée' : `tous modules${jSuffix}`],
      ['Actifs Insight', active, connected ? active/connected : null, connected==null ? 'sur la période' : `des connectés${jSuffix}`],
    ];
    document.getElementById('i_kpis').innerHTML = kpis.map(([l,v,r,d])=>`
      <div class="kpi"><div class="lab">${l}</div><div class="val">${v==null ? '—' : nf.format(v)}</div>
      <div class="rat">${r!=null ? pct(r)+' '+d : (d || '&nbsp;')}</div></div>`).join('');

    lineChart('i_chart', periodDaily(PERIOD[0], PERIOD[1], cid, scopeKeys),
      [['active_users','#6cc79a','Actifs Insight'],['overview_users','#3a7bd5','Quick Overview'],['synthesis_users','#c77d3a','Carte de synthèse']], 'd');

    document.getElementById('i_feat_tb').innerHTML = FEATURES.map(f=>{
      const a = featActions(f.key), u = featCount(f.key);
      return `<tr><td>${f.label}</td><td>${nf.format(u)}</td><td>${active ? pct(u/active) : '—'}</td><td>${nf.format(a)}</td><td>${u ? r2(a/u) : '—'}</td></tr>`;
    }).join('');

    if(!cid){
      gsel.value=''; gsel.disabled=true;
      document.getElementById('i_gran_hint').textContent = 'Sélectionnez un compte pour filtrer par niveau ou périmètre.';
    } else {
      gsel.disabled = perimSel.length>0;
      if(perimSel.length) gsel.value='';
      document.getElementById('i_gran_hint').textContent = perimSel.length ? 'Périmètre actif → agrégation par niveau désactivée.' : '';
    }

    renderValueDriver(cid, perimSel, pTag);
    renderTopDrop(cid, Math.max(connected - active, 0));
    renderAmbass();
    renderRank();
  }

  /* ---------- value driver · Actionnabilité ---------- */
  function prevRange(start, end){
    const s = new Date(start + 'T00:00:00Z'), e = new Date(end + 'T00:00:00Z');
    const span = Math.round((e - s) / 86400000) + 1;
    const pe = new Date(s); pe.setUTCDate(pe.getUTCDate() - 1);
    const ps = new Date(pe); ps.setUTCDate(ps.getUTCDate() - (span - 1));
    const iso = d => d.toISOString().slice(0,10);
    return [iso(ps), iso(pe), span];
  }
  function vdMetrics(rows, spanDays){
    const n = rows.length;
    const sum = k => rows.reduce((s,u)=> s + (u[k] || 0), 0);
    const uW  = k => rows.reduce((s,u)=> s + ((u[k] || 0) > 0 ? 1 : 0), 0);
    const mk = k => { const v = sum(k), u = uW(k); return {v, u, per: u ? v / u : 0}; };
    const totDays = rows.reduce((s,u)=> s + (u.active_days || 0), 0);
    return {n, sy: mk('synthesis'), th: mk('thematic'), ov: mk('overview'),
      freq: { v: n ? (totDays / n) * (30 / spanDays) : 0 }};
  }
  function vdDelta(cur, prev){
    if(prev > 0){
      const d = (cur - prev) / prev;
      if(Math.abs(d) < 0.01) return `<span class="dlt flat">≈ stable <span class="muted">vs période préc.</span></span>`;
      const cls = d > 0 ? 'up' : 'dn', arw = d > 0 ? '▲ ' : '▼ ';
      return `<span class="dlt ${cls}">${arw}${pct(Math.abs(d))} <span class="muted">vs période préc.</span></span>`;
    }
    if(cur > 0) return `<span class="dlt up">nouveau <span class="muted">vs période préc.</span></span>`;
    return `<span class="dlt flat">— <span class="muted">vs période préc.</span></span>`;
  }
  function renderValueDriver(cid, perimSel, pTag){
    document.getElementById('i_vd_h').textContent = `Value driver · Actionnabilité · ${pTag}`;
    const [ps, pe, span] = prevRange(PERIOD[0], PERIOD[1]);
    const cur = vdMetrics(USER_ROWS, span);
    let prevRows = periodUserRows(ps, pe, cid);
    if(perimSel.length){
      const pset = new Set(perimSel);
      prevRows = prevRows.filter(u => (USER_UNITS[u.key]||[]).some(t=>pset.has(t)));
    }
    const prev = vdMetrics(prevRows, span);
    const cards = [
      {lab:'Carte de synthèse consultée', k:'sy', unit:'actions',
       sub:m=>`${nf.format(m.u)} utilisateur(s) · ${r2(m.per)} / utilisateur`},
      {lab:'Thématiques / tendances consultées', k:'th', unit:'actions',
       sub:m=>`${nf.format(m.u)} utilisateur(s) · ${r2(m.per)} / utilisateur`},
      {lab:'Résumés IA lus', k:'ov', unit:'consultations',
       sub:m=>`${nf.format(m.u)} lecteur(s) · ${r2(m.per)} / lecteur`},
    ];
    let h = cards.map(c=>{
      const m = cur[c.k], mp = prev[c.k];
      return `<div class="kpi vd"><div class="lab">${c.lab}</div>
        <div class="val">${nf.format(m.v)}</div>
        <div class="sub2">${c.unit} · ${c.sub(m)}</div>
        ${vdDelta(m.v, mp.v)}</div>`;
    }).join('');
    h += `<div class="kpi vd"><div class="lab">Fréquence de consultation mensuelle</div>
      <div class="val">${cur.freq.v.toFixed(1)} <span class="muted" style="font-size:13px">j / mois</span></div>
      <div class="sub2">jours actifs Insight moyens par utilisateur actif, ramené à 30 j · ${nf.format(cur.n)} actif(s)</div>
      ${vdDelta(cur.freq.v, prev.freq.v)}</div>`;
    document.getElementById('i_vd').innerHTML = h;
    document.getElementById('i_vd_foot').textContent =
      `Signaux : Carte de synthèse = activité « Topic drill-down · overview » ; Thématiques = « Topic drill-down · thematic » ; `
      + `Résumés IA = table Topic Overview Consultations. Fréquence = moyenne des jours distincts avec ≥ 1 signal Insight par utilisateur actif, `
      + `projetée sur 30 j. Périmètre courant : compte / période / périmètre. Période précédente comparée : ${ps} → ${pe} (${span} j).`;
  }

  function renderTopDrop(cid, zero){
    const gran = cid ? gsel.value : '';
    const topH = document.getElementById('i_top_h'), dropH = document.getElementById('i_drop_h');
    const pTag = IS_DEFAULT ? '30 jours' : PLBL;

    if(!gran){
      topH.textContent = `Top adopters — utilisateurs · ${pTag}`;
      dropH.textContent = `Adoption drop-off — utilisateurs · ${pTag}`;
      const withA = USER_ROWS.filter(u=>u.insight_actions>0);
      const desc = withA.slice().sort((a,b)=> b.insight_actions-a.insight_actions || (a.username<b.username?-1:1));
      const asc  = withA.slice().sort((a,b)=> a.insight_actions-b.insight_actions || (a.username<b.username?-1:1));
      const li = u=>`<li>${u.username} <span class="muted">— ${u.customer_name}</span> <span class="n">${nf.format(u.insight_actions)} actions</span></li>`;
      document.getElementById('i_top').innerHTML  = desc.slice(0,3).map(li).join('') || '<li class="muted">Aucun utilisateur actif</li>';
      document.getElementById('i_drop').innerHTML = asc.slice(0,3).map(li).join('')  || '<li class="muted">Aucun utilisateur actif</li>';
      document.getElementById('i_drop_foot').textContent =
        zero>0 ? `+ ${nf.format(zero)} connecté(s) (30 j) sans action Insight sur la période (non listés).` : '';
      return;
    }

    const lbl = LEVEL_LABELS[gran] || gran;
    topH.textContent = `Top adopters — ${lbl} · ${pTag}`;
    dropH.textContent = `Adoption drop-off — ${lbl} · ${pTag}`;
    const all = periodUnitRows(cid, gran);
    const bucket = all.find(u=>u.unit_name===MS);
    const rows = all.filter(u=>u.unit_name!==MS);
    const asc = rows.slice().sort((a,b)=> a.insight_actions-b.insight_actions
      || b.connected_users-a.connected_users || (a.unit_name<b.unit_name?-1:1));
    const desc = rows.slice().sort((a,b)=> b.insight_actions-a.insight_actions
      || b.active_insight_users-a.active_insight_users || (a.unit_name<b.unit_name?-1:1));
    const rate = u => u.connected_users ? pct(u.active_insight_users/u.connected_users) : '—';
    const li = u => `<li>${u.unit_name}`
      + ` <span class="muted">— ${nf.format(u.active_insight_users)}/${nf.format(u.connected_users)} actifs·connectés (30 j) · ${rate(u)} d'adoption ·</span>`
      + ` <span class="n">${nf.format(u.insight_actions)} actions</span></li>`;
    const msLi = bucket ? `<li class="muted" style="list-style:none;margin-left:-20px">— ${MS} : `
      + `${nf.format(bucket.active_insight_users)}/${nf.format(bucket.connected_users)} actifs·connectés (30 j) · ${rate(bucket)} d'adoption, `
      + `${nf.format(bucket.insight_actions)} actions</li>` : '';
    document.getElementById('i_top').innerHTML  = (desc.filter(u=>u.insight_actions>0).slice(0,3).map(li).join('') || '<li class="muted">Aucune unité avec action Insight</li>') + msLi;
    document.getElementById('i_drop').innerHTML = (asc.slice(0,3).map(li).join('') || '<li class="muted">Aucune unité à ce niveau</li>') + msLi;
    document.getElementById('i_drop_foot').textContent =
      `${rows.length} ${lbl} avec ≥ 1 connecté (30 j) · le drop-off inclut les unités à 0 action sur la période. `
      + `Le bucket « ${MS} » est affiché à part, hors classement.`;
  }

  function renderAmbass(){
    document.getElementById('i_ambass').innerHTML = FEATURES.map(f=>{
      const withAct = USER_ROWS.filter(u=>u[f.key]>0).sort((a,b)=>b[f.key]-a[f.key]);
      const amb = withAct.slice(0,3), det = withAct.slice(-3).reverse();
      const li = u=>`<li>${u.username} <span class="muted">— ${u.customer_name}</span> <span class="n">${nf.format(u[f.key])}</span></li>`;
      return `<div style="margin-bottom:14px">
        <div style="font-weight:600;font-size:12.5px;margin-bottom:4px">${f.label}
          <span class="muted">· ${nf.format(withAct.length)} utilisateur(s) avec ≥ 1 action</span></div>
        <div class="grid2">
          <div><div class="muted" style="font-size:11px;text-transform:uppercase">Ambassadeurs</div>
            <ol class="rank">${amb.map(li).join('')||'<li class="muted">—</li>'}</ol></div>
          <div><div class="muted" style="font-size:11px;text-transform:uppercase">Détracteurs (plus faible usage)</div>
            <ol class="rank">${det.map(li).join('')||'<li class="muted">—</li>'}</ol></div>
        </div></div>`;
    }).join('');
  }

  /* ---------- classement (tableau) ---------- */
  const RCOLS_USER=[
    {k:'username',t:'Utilisateur',kind:'txt',name:true},
    {k:'customer_name',t:'Compte',kind:'txt'},
    {k:'role',t:'Rôle',kind:'txt'},
    {k:'n_admin_places',t:'Places',kind:'places'},
    {k:'insight_actions',t:'Actions Insight',kind:'num'},
    {k:'overview',t:'Quick Overview',kind:'num'},
    {k:'synthesis',t:'Synthèse',kind:'num'},
    {k:'thematic',t:'Thématique',kind:'num'},
  ];
  const RCOLS_UNIT=[
    {k:'unit_name',t:'Unité',kind:'txt',name:true},
    {k:'place_count',t:'Places',kind:'places'},
    {k:'connected_users',t:'Connectés',kind:'num'},
    {k:'active_insight_users',t:'Actifs Insight',kind:'num'},
    {k:'rate',t:'Taux d’adoption',kind:'pct'},
    {k:'insight_actions',t:'Actions Insight',kind:'num'},
    {k:'overview_actions',t:'Quick Overview',kind:'num'},
    {k:'synthesis_actions',t:'Synthèse',kind:'num'},
    {k:'thematic_actions',t:'Page thématique',kind:'num'},
  ];

  function placesInfo(u, isUnit){
    if(isUnit){
      const c = u.place_count;
      return {count: (c==null? null : c), names: u.place_names || [], label: u.unit_name};
    }
    const p = USER_PLACES[`${u.username}|${u.customer_id}`] || {total: u.n_admin_places||0, names: []};
    return {count: p.total, names: p.names || [], label: u.username};
  }
  function bindRankSort(){
    document.querySelectorAll('#i_rank_h th').forEach(th=>th.onclick=()=>{
      const k=th.dataset.k; sortAsc=(k===sortK)?!sortAsc:false; sortK=k; renderRank();
    });
  }
  function cmp(a,b){
    let x=a[sortK],y=b[sortK];
    if(typeof x==='string'||typeof y==='string'){x=(x||'')+'';y=(y||'')+'';return sortAsc?x.localeCompare(y):y.localeCompare(x);}
    return sortAsc?(x||0)-(y||0):(y||0)-(x||0);
  }
  function cell(u,c,idx){
    if(c.kind==='txt') return `<td style="text-align:left"${c.name?' class="name"':' class="muted"'}>${u[c.k]||'—'}</td>`;
    if(c.kind==='pct') return `<td>${u.connected_users?pct(u[c.k]||0):'—'}</td>`;
    if(c.kind==='places'){
      const info = placesInfo(u, renderedIsUnit);
      if(info.count==null) return `<td class="muted">—</td>`;
      return `<td class="pcell" data-i="${idx}">${nf.format(info.count)}</td>`;
    }
    return `<td>${nf.format(u[c.k]||0)}</td>`;
  }

  function openPlacesModal(idx){
    const u = renderedRows[idx]; if(!u) return;
    const info = placesInfo(u, renderedIsUnit);
    const shown = info.names.length, more = info.count - shown;
    const cappedByExport = shown >= 50;
    const moreNote = !more ? '' : cappedByExport
      ? `+ ${nf.format(more)} place(s) non listée(s) (limite d'export : 50 noms).`
      : `+ ${nf.format(more)} place(s) non affichée(s) : plusieurs établissements de ce compte partagent le même nom (comptés une seule fois dans la liste).`;
    document.getElementById('i_modal').innerHTML =
      `<div class="modal-bg"><div class="modal">
         <h3>Places — ${info.label}</h3>
         <div class="sub2">${nf.format(info.count)} place(s)${more>0?` · ${nf.format(shown)} affichées`:''}</div>
         <ul>${info.names.map(n=>`<li>${n}</li>`).join('') || '<li class="muted">Noms non disponibles</li>'}</ul>
         ${more>0?`<div class="sub2" style="margin-top:8px">${moreNote}</div>`:''}
         <button id="i_modal_close">Fermer</button>
       </div></div>`;
    document.getElementById('i_modal').hidden = false;
  }
  function closeModal(){ const m=document.getElementById('i_modal'); m.hidden=true; m.innerHTML=''; }
  document.getElementById('i_modal').addEventListener('click', e=>{
    if(e.target.id==='i_modal' || e.target.classList.contains('modal-bg') || e.target.id==='i_modal_close') closeModal();
  });
  document.addEventListener('keydown', e=>{ if(e.key==='Escape') closeModal(); });
  document.getElementById('i_rank_tb').addEventListener('click', e=>{
    const td = e.target.closest('.pcell'); if(td) openPlacesModal(+td.dataset.i);
  });
  function tipText(idx){
    const u = renderedRows[idx]; if(!u) return '';
    const info = placesInfo(u, renderedIsUnit);
    const first = info.names.slice(0,5);
    let t = first.join('\n');
    const more = info.count - first.length;
    if(more>0) t += (t?'\n':'') + `+ ${nf.format(more)} place(s)`;
    if(!info.names.length) t = `${nf.format(info.count)} place(s) · cliquer pour la liste`;
    else t += `\n— cliquer pour tout voir`;
    return t;
  }
  document.getElementById('i_rank_tb').addEventListener('mouseover', e=>{
    const td = e.target.closest('.pcell'); if(!td) return;
    tipEl.textContent = tipText(+td.dataset.i); tipEl.hidden = false;
  });
  document.getElementById('i_rank_tb').addEventListener('mousemove', e=>{
    if(tipEl.hidden) return;
    const pad=14, w=tipEl.offsetWidth, h=tipEl.offsetHeight;
    let x=e.clientX+pad, y=e.clientY+pad;
    if(x+w>innerWidth) x=e.clientX-pad-w;
    if(y+h>innerHeight) y=e.clientY-pad-h;
    tipEl.style.left=x+'px'; tipEl.style.top=y+'px';
  });
  document.getElementById('i_rank_tb').addEventListener('mouseout', e=>{
    if(e.target.closest('.pcell')) tipEl.hidden = true;
  });

  function renderRank(){
    const cid = sel.value, gran = cid ? gsel.value : '';
    renderedIsUnit = !!gran;
    const q = document.getElementById('i_q').value.toLowerCase();
    document.getElementById('i_q').placeholder = gran ? 'Rechercher une unité…' : 'Rechercher un utilisateur…';
    sliderWrap.style.display = gran ? 'none' : '';
    document.getElementById('i_rank_h2').textContent = gran
      ? `Classement d'adoption — ${LEVEL_LABELS[gran]||gran} · ${PLBL}`
      : `Classement d'adoption — utilisateurs · ${PLBL}`;

    const COLS = gran ? RCOLS_UNIT.filter(c => !(gran==='place' && c.k==='place_count')).map(c=>{
      if(!IS_DEFAULT && c.k==='connected_users') return {...c, t:'Connectés (période)'};
      if(!IS_DEFAULT && c.k==='rate') return {...c, t:'Taux (période)'};
      return c;
    }) : RCOLS_USER;
    if(!COLS.some(c=>c.k===sortK)) sortK = 'insight_actions';

    const maxP = +slider.value;
    let rows;
    if(!gran){
      rows = USER_ROWS.filter(u=>u.insight_actions>0)
        .filter(u=>!q || u.username.toLowerCase().includes(q) || (u.customer_name||'').toLowerCase().includes(q))
        .filter(u=> maxP>=10 || (u.n_admin_places||0) <= maxP);
    } else {
      rows = periodUnitRows(cid, gran)
        .filter(u=>!q || (u.unit_name||'').toLowerCase().includes(q));
    }
    rows = rows.slice().sort(cmp);
    renderedRows = rows;

    document.getElementById('i_rank_h').innerHTML = COLS.map(c=>`<th data-k="${c.k}">${c.t}</th>`).join('');
    bindRankSort();
    document.getElementById('i_rank_tb').innerHTML =
      rows.slice(0,500).map((u,i)=>'<tr>'+COLS.map(c=>cell(u,c,i)).join('')+'</tr>').join('');
    document.querySelectorAll('#i_rank_h th').forEach(th=>{
      th.classList.toggle('sorted',th.dataset.k===sortK);
      th.classList.toggle('asc',th.dataset.k===sortK&&sortAsc);});
    const slFoot = (!gran && maxP<10) ? ` · filtre : ≤ ${slider.value} place(s)` : '';
    const denomNote = (gran && !IS_DEFAULT) ? ' · connectés recalculés sur la période' : '';
    const placeNote = (gran==='place') ? ' · regroupement par nom d’établissement (deux fiches homonymes chez un même compte comptent comme une seule ligne)' : '';
    document.getElementById('i_rank_foot').textContent = gran
      ? `${rows.length} ${LEVEL_LABELS[gran]||gran} · classement exhaustif${denomNote}${placeNote}` + (rows.length>500?' (500 affichées)':'')
      : `${rows.length} utilisateur(s) avec action Insight sur la période` + slFoot + (rows.length>500?' (500 affichés)':'');
  }

  function applyFilters(f){
    if(f.customer !== undefined){
      const has = [...sel.options].some(o=>o.value===f.customer);
      sel.value = has ? f.customer : '';
    }
    if(f.period){ perSel.value = f.period; document.getElementById('i_custom_wrap').hidden = perSel.value!=='custom'; }
    if(f.from) fromEl.value = f.from;
    if(f.to) toEl.value = f.to;
    const cid = sel.value;
    usel.populate(cid, PERIMETERS);
    usel.disabled = !cid;
    if(cid && f.perim && f.perim.length) usel.setValues(f.perim);
    if(cid && !usel.values.length && f.gran) gsel.value = f.gran;
    render();
  }
  registerFilterSync('insight', applyFilters);
  applyFilters(SHARED_FILTERS);
})();


/* ======================================================= E-REPUTATION (lazy) */
function initErep(){
  const EREP = window.__EREP__ || {};
  const FEATURES = [
    {key:'overview',  label:'Note Google'},
    {key:'synthesis', label:'Benchmark concurrentiel'},
  ];
  const salFrom = s => { const a = new Array(9).fill(null); (s||[]).forEach(p=> a[p[0]] = p[1]); return a; };
  function accScope(k){
    const c2 = sel.value ? custs.filter(c=>c.customer_id===sel.value) : custs;
    return c2.reduce((s,c)=>s+(c[k]||0),0);
  }
  const custs = EREP.customers.slice().sort((a,b)=>b.connected_users-a.connected_users);
  const UNITS = EREP.units || [];
  const USER_UNITS = EREP.user_units || {};
  const PERIMETERS = EREP.perimeters || [];
  // dénominateurs "connectés" par période — index : 0=30j, 1=mois préc., 2=trimestre, 3=année
  const CONN_PERIOD = EREP.connected_period || {};
  const CONN_PERIOD_UNIT = (() => {
    const m = new Map();
    for(const r of (EREP.connected_period_unit || [])) m.set(r[0] + '|' + r[1], [r[2], r[3], r[4], r[5]]);
    return m;
  })();
  const PERIOD_IDX = {'30d':0, 'prevmonth':1, 'quarter':2, 'year':3};
  // Insight/E-rép : les actifs sont recalculés côté client sur la période choisie,
  // le dénominateur doit donc suivre. Période "custom" -> undefined -> ratio masqué.
  function connIdx(){ return PERIOD_IDX[perSel.value]; }
  const DU = EREP.daily_user || [];
  const UDIM = EREP.user_dim || {};
  const USER_PLACES = EREP.user_places || {};
  const SAL_IDX = {place:0,zone:1,sector:2,subtype:3,region:4,department:5,country:6,type:7,brand:8};
  const GOOGLE_SNAPSHOT = EREP.google_place_snapshot || [];
  const GOOGLE_CUSTOMER_DAY = EREP.google_customer_day || [];
  const GOOGLE_PERIMETER_30D = EREP.google_perimeter_30d || [];
  const DATA_MAX = EREP.data_max || new Date().toISOString().slice(0,10);
  const DATA_MIN = EREP.data_min || DATA_MAX;
  const LEVEL_LABELS = {place:'places',zone:'zones',sector:'secteurs',subtype:'sous-types',
    region:'régions',department:'départements',country:'pays',type:'types',brand:'brand levels'};
  const LEVEL_SING = {place:'Place',zone:'Zone',sector:'Secteur',subtype:'Sous-type',
    region:'Région',department:'Département',country:'Pays',type:'Type',brand:'Brand level'};
  const PLABELS = {'30d':'30 derniers jours','prevmonth':'mois précédent','quarter':'trimestre actuel',
    'year':'année courante','custom':'période custom'};
  const MS = '(accès multi-strates)';

  const sel = document.getElementById('e_customer');
  const gsel = document.getElementById('e_gran');
  const usel = makePerim('e', () => { syncFilters('erep', {perim: usel.values}); render(); }, LEVEL_SING);
  const perSel = document.getElementById('e_period');
  const fromEl = document.getElementById('e_from'), toEl = document.getElementById('e_to');
  const slider = document.getElementById('e_places');
  const sliderWrap = document.getElementById('e_slider_wrap');
  const tipEl = document.getElementById('e_tip');

  sel.add(new Option(`Tous les comptes éligibles (${custs.length})`, ''));
  custs.slice().sort((a,b)=>a.customer_name.localeCompare(b.customer_name)).forEach(c=>sel.add(new Option(`${c.customer_name} — ${nf.format(c.active_insight_users)} actifs (30 j)`, c.customer_id)));
  fromEl.min = toEl.min = DATA_MIN; fromEl.max = toEl.max = DATA_MAX;
  fromEl.value = DATA_MIN; toEl.value = DATA_MAX;

  sel.onchange = () => { syncFilters('erep', {customer: sel.value, perim: [], gran: ''}); render(); };
  gsel.onchange = () => { syncFilters('erep', {gran: gsel.value}); render(); };
  perSel.onchange = ()=>{ document.getElementById('e_custom_wrap').hidden = perSel.value!=='custom'; syncFilters('erep', {period: perSel.value}); render(); };
  fromEl.oninput = toEl.oninput = ()=>{ syncFilters('erep', {from: fromEl.value, to: toEl.value}); render(); };
  document.getElementById('e_q').oninput = renderRank;
  slider.oninput = ()=>{ document.getElementById('e_places_val').textContent = slider.value==='10'?'10+':slider.value; renderRank(); };

  document.getElementById('e_disclaimer').textContent =
    "Module E-réputation Google. Actif = au moins 1 activité Metric GOOGLE_SCORE ou Metric GOOGLE_BENCHMARK sur la période. "
    + "Connecté = présence Back Office globale (dénominateur sur 30 jours). "
    + "Fonctionnalités : Note Google (GOOGLE_SCORE — accès si l'utilisateur administre au moins 1 place mappée à une fiche Google) ; "
    + "Benchmark concurrentiel (GOOGLE_BENCHMARK — accès si le benchmark est configuré au niveau du compte). "
    + "L'accessibilité n'est appliquée qu'au bloc Usage par fonctionnalité (colonne Adoption accès) et aux détracteurs par fonctionnalité. "
    + "Filtre de période et granularité identiques au module Insight.";

  let sortK='insight_actions', sortAsc=false;
  let USER_ROWS=[], renderedRows=[], renderedIsUnit=false;
  let PERIOD=['',''], PLBL='', IS_DEFAULT=true;

  /* ---------- période ---------- */
  function periodRange(){
    const iso = dt => dt.toISOString().slice(0,10);
    const emax = new Date(DATA_MAX + 'T00:00:00Z');
    const p = perSel.value;
    if(p === 'custom') return [fromEl.value || DATA_MIN, toEl.value || DATA_MAX];
    if(p === 'prevmonth'){
      const y=emax.getUTCFullYear(), m=emax.getUTCMonth();
      return [iso(new Date(Date.UTC(y, m-1, 1))), iso(new Date(Date.UTC(y, m, 0)))];
    }
    if(p === 'quarter'){
      const y=emax.getUTCFullYear(), q=Math.floor(emax.getUTCMonth()/3);
      return [iso(new Date(Date.UTC(y, q*3, 1))), DATA_MAX];
    }
    if(p === 'year') return [iso(new Date(Date.UTC(emax.getUTCFullYear(), 0, 1))), DATA_MAX];
    const s = new Date(emax); s.setUTCDate(s.getUTCDate() - 29);   // 30 j glissants inclus
    return [iso(s), DATA_MAX];
  }

  function periodUserRows(start, end, cid){
    const acc = new Map();
    for(const r of DU){
      if(r.d < start || r.d > end) continue;
      if(cid && r.k.split('|')[1] !== cid) continue;
      let o = acc.get(r.k);
      if(!o){ o = {ov:0,sy:0,th:0,mv:0}; acc.set(r.k, o); }
      o.ov+=r.ov||0; o.sy+=r.sy||0; o.th+=r.th||0; o.mv+=r.mv||0;
    }
    const out = [];
    for(const [key, a] of acc){
      const [username, customer_id] = key.split('|');
      const d = UDIM[key] || {};
      out.push({key, username, customer_id, customer_name: d.cn || '—', role: d.role || '',
        n_admin_places: d.np || 0, cgs: d.cgs, be: d.be, sal: salFrom(d.s),
        overview: a.ov, synthesis: a.sy, thematic: a.th, monitored_views: a.mv,
        insight_actions: a.ov + a.sy + a.th});
    }
    return out;
  }

  function periodDaily(start, end, cid, keySet){
    const byDay = new Map();
    for(const r of DU){
      if(r.d < start || r.d > end) continue;
      if(cid && r.k.split('|')[1] !== cid) continue;
      if(keySet && !keySet.has(r.k)) continue;
      let o = byDay.get(r.d);
      if(!o){ o = {d:r.d, act:new Set(), ov:new Set(), sy:new Set()}; byDay.set(r.d, o); }
      if((r.ov||0)+(r.sy||0)+(r.th||0)+(r.mv||0) > 0) o.act.add(r.k);
      if(r.ov > 0) o.ov.add(r.k);
      if(r.sy > 0) o.sy.add(r.k);
    }
    return [...byDay.values()].sort((a,b)=> a.d < b.d ? -1 : 1)
      .map(o=>({d:o.d, active_users:o.act.size, overview_users:o.ov.size, synthesis_users:o.sy.size}));
  }

  function connFor(cid){
    // Le dénominateur suit la période choisie (corrigé 2026-09-17) : auparavant il
    // restait figé à 30 j pendant que le numérateur "actifs" suivait la période,
    // ce qui gonflait le ratio (et le faisait dépasser 100 % sur certains comptes).
    // Période "custom" : non précalculable -> null, le ratio est alors masqué.
    const pi = connIdx();
    if(pi === undefined) return null;
    const cs = cid ? custs.filter(c=>c.customer_id===cid) : custs;
    return cs.reduce((s,c)=>{
      const a = CONN_PERIOD[c.customer_id];
      return s + (a ? (a[pi] || 0) : 0);
    }, 0);
  }
  function connForUnits(cid, tokens){
    const pi = connIdx();
    if(pi === undefined) return null;
    let s = 0;
    for(const t of tokens){
      const a = CONN_PERIOD_UNIT.get(cid + '|' + t);
      if(a) s += a[pi] || 0;
    }
    return s;
  }
  function ctxLabel(cid){
    const cs = cid ? custs.filter(c=>c.customer_id===cid) : custs;
    return cid ? (cs[0] ? cs[0].customer_name : '—') : `${cs.length} comptes`;
  }
  function rosterFor(cid){
    const cs = cid ? custs.filter(c=>c.customer_id===cid) : custs;
    return cs.reduce((s,c)=>s+(c.roster||0), 0);
  }

  /* ---------- value driver · Acquisition (note Google / avis / réponse) ---------- */
  function prevRangeG(start, end){
    const s = new Date(start + 'T00:00:00Z'), e = new Date(end + 'T00:00:00Z');
    const span = Math.round((e - s) / 86400000) + 1;
    const pe = new Date(s); pe.setUTCDate(pe.getUTCDate() - 1);
    const ps = new Date(pe); ps.setUTCDate(ps.getUTCDate() - (span - 1));
    const iso = d => d.toISOString().slice(0,10);
    return [iso(ps), iso(pe), span];
  }
  function gDeltaLbl(cur, prev, lbl){
    if(prev > 0){
      const d = (cur - prev) / prev;
      if(Math.abs(d) < 0.01) return `<span class="dlt flat">≈ stable <span class="muted">${lbl}</span></span>`;
      const cls = d > 0 ? 'up' : 'dn', arw = d > 0 ? '▲ ' : '▼ ';
      return `<span class="dlt ${cls}">${arw}${pct(Math.abs(d))} <span class="muted">${lbl}</span></span>`;
    }
    if(cur > 0) return `<span class="dlt up">nouveau <span class="muted">${lbl}</span></span>`;
    return `<span class="dlt flat">— <span class="muted">${lbl}</span></span>`;
  }
  function placesForScope(cid, perimSel){
    let rows = cid ? GOOGLE_SNAPSHOT.filter(p=>p.c===cid) : GOOGLE_SNAPSHOT;
    if(cid && perimSel.length){
      const toks = perimSel.map(t=>{ const i=t.indexOf('\u0001'); return [t.slice(0,i), t.slice(i+1)]; });
      rows = rows.filter(p => toks.some(([lv,nm]) => p.u[SAL_IDX[lv]] === nm));
    }
    return rows;
  }
  function weightedScore(rows, key){
    let num=0, den=0;
    for(const p of rows){ if(p[key]!=null && p.rv){ num += p[key]*p.rv; den += p.rv; } }
    return den ? num/den : null;
  }
  function reviewStatsForScope(cid, perimSel, period){
    if(cid && perimSel.length){
      const pset = new Set(perimSel);
      const rows = GOOGLE_PERIMETER_30D.filter(r=>r.customer_id===cid && pset.has(r.level+'\u0001'+r.unit_name));
      const sum = k => rows.reduce((s,r)=>s+(r[k]||0),0);
      return { fixed30: true,
        reviews: sum('reviews_30d'), replied: sum('replied_30d'), replyDays: sum('reply_days_30d'),
        prevReviews: sum('reviews_prev30d'), prevReplied: sum('replied_prev30d'), prevReplyDays: sum('reply_days_prev30d') };
    }
    const [ps, pe] = prevRangeG(period[0], period[1]);
    const agg = (start, end) => {
      let n=0, r=0, s=0;
      for(const row of GOOGLE_CUSTOMER_DAY){
        if(row.d < start || row.d > end) continue;
        if(cid && row.k !== cid) continue;
        n += row.n||0; r += row.r||0; s += row.s||0;
      }
      return {n, r, s};
    };
    const cur = agg(period[0], period[1]), prev = agg(ps, pe);
    return { fixed30: false, ps, pe,
      reviews: cur.n, replied: cur.r, replyDays: cur.s,
      prevReviews: prev.n, prevReplied: prev.r, prevReplyDays: prev.s };
  }
  function renderValueDriverAcquisition(cid, perimSel, pTag){
    const dlbl = (perimSel.length ? 'vs 30 j précédents' : 'vs période préc.');
    document.getElementById('e_vd_h').textContent =
      `Value driver · Acquisition · ${perimSel.length ? '30 jours (périmètre)' : pTag}`;
    const rows = placesForScope(cid, perimSel);
    const score = weightedScore(rows, 'sc');
    const scoreLy = weightedScore(rows, 'sly');
    const st = reviewStatsForScope(cid, perimSel, PERIOD);
    const taux = st.reviews ? st.replied / st.reviews : null;
    const tauxPrev = st.prevReviews ? st.prevReplied / st.prevReviews : null;
    const temps = st.replied ? st.replyDays / st.replied : null;
    const tempsPrev = st.prevReplied ? st.prevReplyDays / st.prevReplied : null;
    const cards = [];
    cards.push(`<div class="kpi vd"><div class="lab">Note Google moyenne</div>
      <div class="val">${score!=null ? score.toFixed(2) : '—'} <span class="muted" style="font-size:13px">/5</span></div>
      <div class="sub2">pondérée par volume d'avis · ${nf.format(rows.reduce((s,p)=>s+(p.rv||0),0))} avis cumulés</div>
      ${score!=null && scoreLy!=null ? gDeltaLbl(score, scoreLy, 'vs il y a 12 mois') : '<span class="dlt flat">— <span class="muted">vs il y a 12 mois</span></span>'}</div>`);
    cards.push(`<div class="kpi vd"><div class="lab">Volume d'avis reçus</div>
      <div class="val">${nf.format(st.reviews)}</div>
      <div class="sub2">avis Google collectés sur la période</div>
      ${gDeltaLbl(st.reviews, st.prevReviews, dlbl)}</div>`);
    cards.push(`<div class="kpi vd"><div class="lab">Taux de réponse aux avis Google</div>
      <div class="val">${taux!=null ? pct(taux) : '—'}</div>
      <div class="sub2">${nf.format(st.replied)} / ${nf.format(st.reviews)} avis répondus</div>
      ${taux!=null && tauxPrev!=null ? gDeltaLbl(taux, tauxPrev, dlbl) : '<span class="dlt flat">— <span class="muted">'+dlbl+'</span></span>'}</div>`);
    cards.push(`<div class="kpi vd"><div class="lab">Temps de réponse moyen</div>
      <div class="val">${temps!=null ? r2(temps) : '—'} <span class="muted" style="font-size:13px">j</span></div>
      <div class="sub2">délai moyen avis → réponse, sur les avis répondus</div>
      ${temps!=null && tempsPrev!=null ? gDeltaLbl(temps, tempsPrev, dlbl) : '<span class="dlt flat">— <span class="muted">'+dlbl+'</span></span>'}</div>`);
    document.getElementById('e_vd').innerHTML = cards.join('');
    document.getElementById('e_vd_foot').textContent =
      `Note Google = snapshot du dernier mois clos (indépendant du filtre période), moyenne pondérée par le volume d'avis de chaque établissement du périmètre. `
      + `Volume/taux/temps de réponse = avis Google (PARTICIPATIONS, canal Google/GoogleMyBusiness). `
      + (perimSel.length ? `Un périmètre est actif → volume/taux/temps figés sur 30 j glissants (comme les dénominateurs « connectés »), indépendamment du filtre période. `
                          : `Période comparée : ${st.ps||'—'} → ${st.pe||'—'}. `)
      + `Benchmark concurrentiel (score comparatif) non stocké côté data — seule sa consultation est trackée (cf. « Usage par fonctionnalité » et « Actifs E-rép » ci-dessus).`;
  }
  function renderGoogleTopFlop(cid, perimSel){
    const MIN_REVIEWS = 5;
    const rows = placesForScope(cid, perimSel).filter(p => p.sc != null && (p.rv||0) >= MIN_REVIEWS);
    const desc = rows.slice().sort((a,b)=> b.sc - a.sc || (b.rv - a.rv));
    const asc  = rows.slice().sort((a,b)=> a.sc - b.sc || (b.rv - a.rv));
    const li = p => `<li>${p.u[0] || '—'} <span class="muted">— ${nf.format(p.rv||0)} avis</span> <span class="n">${p.sc.toFixed(2)}/5</span></li>`;
    document.getElementById('e_gtop').innerHTML  = desc.slice(0,5).map(li).join('') || '<li class="muted">Aucun établissement éligible</li>';
    document.getElementById('e_gflop').innerHTML = asc.slice(0,5).map(li).join('')  || '<li class="muted">Aucun établissement éligible</li>';
    document.getElementById('e_gtopflop_foot').textContent =
      `${nf.format(rows.length)} établissement(s) du périmètre avec ≥ ${MIN_REVIEWS} avis Google (seuil pour éviter qu'un établissement à très faible volume fausse le classement).`;
  }


  function unitsForLevel(u, gran){
    // rattachement hiérarchique (option B, comme le Périmètre) — un utilisateur
    // peut appartenir à plusieurs unités du même niveau (ex. admin de 2 régions).
    const toks = USER_UNITS[u.key];
    if(!toks || !toks.length) return [];
    const out = [];
    for(const t of toks){
      const sep = t.indexOf('\u0001');
      if(t.slice(0, sep) === gran) out.push(t.slice(sep + 1));
    }
    return out;
  }
  function periodUnitRows(cid, gran){
    const byUnit = new Map();
    for(const u of USER_ROWS){
      const names = unitsForLevel(u, gran);
      for(const name of names){
        let o = byUnit.get(name);
        if(!o){ o = {ai:0,ia:0,ov:0,sy:0,th:0}; byUnit.set(name, o); }
        if(u.insight_actions + u.monitored_views > 0) o.ai += 1;
        o.ia += u.insight_actions; o.ov += u.overview; o.sy += u.synthesis; o.th += u.thematic;
      }
    }
    const pi = connIdx();
    return UNITS.filter(x=>x.customer_id===cid && x.level===gran).map(x=>{
      const p = byUnit.get(x.unit_name) || {ai:0,ia:0,ov:0,sy:0,th:0};
      // dénominateur par unité aligné sur la période sélectionnée (2026-09-17)
      const cp = pi===undefined ? null : CONN_PERIOD_UNIT.get(cid + '|' + gran + '\u0001' + x.unit_name);
      const conn = pi===undefined ? null : (cp ? (cp[pi] || 0) : 0);
      return {unit_name:x.unit_name, place_count:x.place_count, place_names:x.place_names,
        connected_users:conn,
        active_insight_users:p.ai, insight_actions:p.ia,
        overview_actions:p.ov, synthesis_actions:p.sy, thematic_actions:p.th,
        rate: conn ? p.ai / conn : 0};
    });
  }

  /* ---------- render principal ---------- */
  function render(){
    const cid = sel.value;
    if(usel.dataset.cid !== (cid||'')) usel.populate(cid, PERIMETERS);
    usel.disabled = !cid;
    PERIOD = periodRange();
    IS_DEFAULT = perSel.value === '30d';
    PLBL = PLABELS[perSel.value];
    document.getElementById('e_custom_wrap').hidden = perSel.value !== 'custom';
    document.getElementById('e_period_dates').textContent = IS_DEFAULT
      ? 'fenêtre glissante' : `${PERIOD[0]} → ${PERIOD[1]}`;
    const pTag = IS_DEFAULT ? '30 jours' : PLBL;
    document.getElementById('e_chart_h').textContent = `Utilisateurs actifs E-réputation — quotidien · ${pTag}`;
    document.getElementById('e_feat_h').textContent = `Actifs par fonctionnalité · ${pTag}`;

    USER_ROWS = periodUserRows(PERIOD[0], PERIOD[1], cid);
    const perimSel = cid ? usel.values : [];
    let unitScope = null;
    if(perimSel.length){
      const pset = new Set(perimSel);
      USER_ROWS = USER_ROWS.filter(u => (USER_UNITS[u.key]||[]).some(t=>pset.has(t)));
      const prows = PERIMETERS.filter(p=>p.customer_id===cid && pset.has(p.level+'\u0001'+p.unit_name));
      unitScope = { rows: prows, label: perimSel.length===1
        ? LEVEL_SING[perimSel[0].split('\u0001')[0]] + ' « ' + perimSel[0].split('\u0001')[1] + ' »'
        : perimSel.length + ' unités' };
    }
    const scopeP = unitScope ? {
      connected_users: connForUnits(cid, perimSel),
      connected_score_access: unitScope.rows.reduce((s,p)=>s+(p.connected_score_access||0),0),
      connected_bench_access: unitScope.rows.reduce((s,p)=>s+(p.connected_bench_access||0),0),
    } : null;
    const scopeKeys = unitScope ? new Set(USER_ROWS.map(u=>u.key)) : null;
    const active = USER_ROWS.length;
    const connected = scopeP ? scopeP.connected_users : connFor(cid);
    // Le dénominateur suit désormais la période (2026-09-17). Seule la période
    // "custom" n'est pas précalculable : connected vaut null et le ratio est masqué
    // plutôt que d'afficher un pourcentage faux.
    const jSuffix = IS_DEFAULT ? '' : ' (période)';
    const featCount = k => USER_ROWS.reduce((s,u)=> s + (u[k] > 0 ? 1 : 0), 0);
    const featActions = k => USER_ROWS.reduce((s,u)=> s + (u[k] || 0), 0);

    document.getElementById('e_ctx').textContent =
      (cid ? `${ctxLabel(cid)} · ${nf.format(rosterFor(cid))} comptes créés · ` : `${ctxLabel(cid)} · `)
      + `${connected==null ? '—' : nf.format(connected)} connectés${jSuffix} · période : ${IS_DEFAULT ? '30 j' : PERIOD[0]+' → '+PERIOD[1]}`
      + (unitScope ? ` · périmètre : ${unitScope.label}` + (perimSel.length>1 ? ' (connectés = somme des unités)' : '') : '');

    const kpis = [
      ['Connectés', connected, null, connected==null ? 'non calculable sur période personnalisée' : `tous modules${jSuffix}`],
      ['Actifs E-rép', active, connected ? active/connected : null, connected==null ? 'sur la période' : `des connectés${jSuffix}`],
    ];
    document.getElementById('e_kpis').innerHTML = kpis.map(([l,v,r,d])=>`
      <div class="kpi"><div class="lab">${l}</div><div class="val">${v==null ? '—' : nf.format(v)}</div>
      <div class="rat">${r!=null ? pct(r)+' '+d : (d || '&nbsp;')}</div></div>`).join('');

    lineChart('e_chart', periodDaily(PERIOD[0], PERIOD[1], cid, scopeKeys),
      [['active_users','#6cc79a','Actifs E-rép'],['overview_users','#3a7bd5','Note Google'],['synthesis_users','#c77d3a','Benchmark']], 'd');

    document.getElementById('e_feat_tb').innerHTML = FEATURES.map(f=>{
      const a = featActions(f.key), u = featCount(f.key);
      const accDen = scopeP
        ? (scopeP[f.key==='overview' ? 'connected_score_access' : 'connected_bench_access'] || 0)
        : accScope(f.key==='overview' ? 'connected_score_access' : 'connected_bench_access');
      return `<tr><td>${f.label}</td><td>${nf.format(u)}</td><td>${active ? pct(u/active) : '—'}</td><td>${nf.format(a)}</td><td>${u ? r2(a/u) : '—'}</td>`
        + `<td>${accDen ? pct(u/accDen) : '—'} <span class="muted" style="font-size:11px">(${nf.format(accDen)})</span></td></tr>`;
    }).join('');

    if(!cid){
      gsel.value=''; gsel.disabled=true;
      document.getElementById('e_gran_hint').textContent = 'Sélectionnez un compte pour filtrer par niveau ou périmètre.';
    } else {
      gsel.disabled = perimSel.length>0;
      if(perimSel.length) gsel.value='';
      document.getElementById('e_gran_hint').textContent = perimSel.length ? 'Périmètre actif → agrégation par niveau désactivée.' : '';
    }

    renderValueDriverAcquisition(cid, perimSel, pTag);
    renderGoogleTopFlop(cid, perimSel);
    renderTopDrop(cid, Math.max(connected - active, 0));
    renderAmbass();
    renderRank();
  }

  function renderTopDrop(cid, zero){
    const gran = cid ? gsel.value : '';
    const topH = document.getElementById('e_top_h'), dropH = document.getElementById('e_drop_h');
    const pTag = IS_DEFAULT ? '30 jours' : PLBL;

    if(!gran){
      topH.textContent = `Top adopters — utilisateurs · ${pTag}`;
      dropH.textContent = `Adoption drop-off — utilisateurs · ${pTag}`;
      const withA = USER_ROWS.filter(u=>u.insight_actions>0);
      const desc = withA.slice().sort((a,b)=> b.insight_actions-a.insight_actions || (a.username<b.username?-1:1));
      const asc  = withA.slice().sort((a,b)=> a.insight_actions-b.insight_actions || (a.username<b.username?-1:1));
      const li = u=>`<li>${u.username} <span class="muted">— ${u.customer_name}</span> <span class="n">${nf.format(u.insight_actions)} actions</span></li>`;
      document.getElementById('e_top').innerHTML  = desc.slice(0,3).map(li).join('') || '<li class="muted">Aucun utilisateur actif</li>';
      document.getElementById('e_drop').innerHTML = asc.slice(0,3).map(li).join('')  || '<li class="muted">Aucun utilisateur actif</li>';
      document.getElementById('e_drop_foot').textContent =
        zero>0 ? `+ ${nf.format(zero)} connecté(s) (30 j) sans action E-réputation sur la période (non listés).` : '';
      return;
    }

    const lbl = LEVEL_LABELS[gran] || gran;
    topH.textContent = `Top adopters — ${lbl} · ${pTag}`;
    dropH.textContent = `Adoption drop-off — ${lbl} · ${pTag}`;
    const all = periodUnitRows(cid, gran);
    const bucket = all.find(u=>u.unit_name===MS);
    const rows = all.filter(u=>u.unit_name!==MS);
    const asc = rows.slice().sort((a,b)=> a.insight_actions-b.insight_actions
      || b.connected_users-a.connected_users || (a.unit_name<b.unit_name?-1:1));
    const desc = rows.slice().sort((a,b)=> b.insight_actions-a.insight_actions
      || b.active_insight_users-a.active_insight_users || (a.unit_name<b.unit_name?-1:1));
    const rate = u => u.connected_users ? pct(u.active_insight_users/u.connected_users) : '—';
    const li = u => `<li>${u.unit_name}`
      + ` <span class="muted">— ${nf.format(u.active_insight_users)}/${nf.format(u.connected_users)} actifs·connectés (30 j) · ${rate(u)} d'adoption ·</span>`
      + ` <span class="n">${nf.format(u.insight_actions)} actions</span></li>`;
    const msLi = bucket ? `<li class="muted" style="list-style:none;margin-left:-20px">— ${MS} : `
      + `${nf.format(bucket.active_insight_users)}/${nf.format(bucket.connected_users)} actifs·connectés (30 j) · ${rate(bucket)} d'adoption, `
      + `${nf.format(bucket.insight_actions)} actions</li>` : '';
    document.getElementById('e_top').innerHTML  = (desc.filter(u=>u.insight_actions>0).slice(0,3).map(li).join('') || '<li class="muted">Aucune unité avec action E-réputation</li>') + msLi;
    document.getElementById('e_drop').innerHTML = (asc.slice(0,3).map(li).join('') || '<li class="muted">Aucune unité à ce niveau</li>') + msLi;
    document.getElementById('e_drop_foot').textContent =
      `${rows.length} ${lbl} avec ≥ 1 connecté (30 j) · le drop-off inclut les unités à 0 action sur la période. `
      + `Le bucket « ${MS} » est affiché à part, hors classement.`;
  }

  function renderAmbass(){
    document.getElementById('e_ambass').innerHTML = FEATURES.map(f=>{
      const accK = f.key==='overview' ? 'cgs' : 'be';
      const pool = USER_ROWS.filter(u=>u[accK]);
      const withAct = pool.filter(u=>u[f.key]>0).sort((a,b)=>b[f.key]-a[f.key]);
      const amb = withAct.slice(0,3);
      const det = pool.slice().sort((a,b)=>(a[f.key]||0)-(b[f.key]||0)).slice(0,3);
      const li = u=>`<li>${u.username} <span class="muted">— ${u.customer_name}</span> <span class="n">${nf.format(u[f.key])}</span></li>`;
      return `<div style="margin-bottom:14px">
        <div style="font-weight:600;font-size:12.5px;margin-bottom:4px">${f.label}
          <span class="muted">· ${nf.format(withAct.length)} utilisateur(s) avec ≥ 1 action</span></div>
        <div class="grid2">
          <div><div class="muted" style="font-size:11px;text-transform:uppercase">Ambassadeurs</div>
            <ol class="rank">${amb.map(li).join('')||'<li class="muted">—</li>'}</ol></div>
          <div><div class="muted" style="font-size:11px;text-transform:uppercase">Détracteurs (plus faible usage)</div>
            <ol class="rank">${det.map(li).join('')||'<li class="muted">—</li>'}</ol></div>
        </div></div>`;
    }).join('');
  }

  /* ---------- classement (tableau) ---------- */
  const RCOLS_USER=[
    {k:'username',t:'Utilisateur',kind:'txt',name:true},
    {k:'customer_name',t:'Compte',kind:'txt'},
    {k:'role',t:'Rôle',kind:'txt'},
    {k:'n_admin_places',t:'Places',kind:'places'},
    {k:'insight_actions',t:'Actions E-rép',kind:'num'},
    {k:'overview',t:'Note Google',kind:'num'},
    {k:'synthesis',t:'Benchmark',kind:'num'},
  ];
  const RCOLS_UNIT=[
    {k:'unit_name',t:'Unité',kind:'txt',name:true},
    {k:'place_count',t:'Places',kind:'places'},
    {k:'connected_users',t:'Connectés',kind:'num'},
    {k:'active_insight_users',t:'Actifs E-rép',kind:'num'},
    {k:'rate',t:'Taux d’adoption',kind:'pct'},
    {k:'insight_actions',t:'Actions E-rép',kind:'num'},
    {k:'overview_actions',t:'Note Google',kind:'num'},
    {k:'synthesis_actions',t:'Benchmark',kind:'num'},
  ];

  function placesInfo(u, isUnit){
    if(isUnit){
      const c = u.place_count;
      return {count: (c==null? null : c), names: u.place_names || [], label: u.unit_name};
    }
    const p = USER_PLACES[`${u.username}|${u.customer_id}`] || {total: u.n_admin_places||0, names: []};
    return {count: p.total, names: p.names || [], label: u.username};
  }
  function bindRankSort(){
    document.querySelectorAll('#e_rank_h th').forEach(th=>th.onclick=()=>{
      const k=th.dataset.k; sortAsc=(k===sortK)?!sortAsc:false; sortK=k; renderRank();
    });
  }
  function cmp(a,b){
    let x=a[sortK],y=b[sortK];
    if(typeof x==='string'||typeof y==='string'){x=(x||'')+'';y=(y||'')+'';return sortAsc?x.localeCompare(y):y.localeCompare(x);}
    return sortAsc?(x||0)-(y||0):(y||0)-(x||0);
  }
  function cell(u,c,idx){
    if(c.kind==='txt') return `<td style="text-align:left"${c.name?' class="name"':' class="muted"'}>${u[c.k]||'—'}</td>`;
    if(c.kind==='pct') return `<td>${u.connected_users?pct(u[c.k]||0):'—'}</td>`;
    if(c.kind==='places'){
      const info = placesInfo(u, renderedIsUnit);
      if(info.count==null) return `<td class="muted">—</td>`;
      return `<td class="pcell" data-i="${idx}">${nf.format(info.count)}</td>`;
    }
    return `<td>${nf.format(u[c.k]||0)}</td>`;
  }

  function openPlacesModal(idx){
    const u = renderedRows[idx]; if(!u) return;
    const info = placesInfo(u, renderedIsUnit);
    const shown = info.names.length, more = info.count - shown;
    const cappedByExport = shown >= 50;
    const moreNote = !more ? '' : cappedByExport
      ? `+ ${nf.format(more)} place(s) non listée(s) (limite d'export : 50 noms).`
      : `+ ${nf.format(more)} place(s) non affichée(s) : plusieurs établissements de ce compte partagent le même nom (comptés une seule fois dans la liste).`;
    document.getElementById('e_modal').innerHTML =
      `<div class="modal-bg"><div class="modal">
         <h3>Places — ${info.label}</h3>
         <div class="sub2">${nf.format(info.count)} place(s)${more>0?` · ${nf.format(shown)} affichées`:''}</div>
         <ul>${info.names.map(n=>`<li>${n}</li>`).join('') || '<li class="muted">Noms non disponibles</li>'}</ul>
         ${more>0?`<div class="sub2" style="margin-top:8px">${moreNote}</div>`:''}
         <button id="e_modal_close">Fermer</button>
       </div></div>`;
    document.getElementById('e_modal').hidden = false;
  }
  function closeModal(){ const m=document.getElementById('e_modal'); m.hidden=true; m.innerHTML=''; }
  document.getElementById('e_modal').addEventListener('click', e=>{
    if(e.target.id==='e_modal' || e.target.classList.contains('modal-bg') || e.target.id==='e_modal_close') closeModal();
  });
  document.addEventListener('keydown', e=>{ if(e.key==='Escape') closeModal(); });
  document.getElementById('e_rank_tb').addEventListener('click', e=>{
    const td = e.target.closest('.pcell'); if(td) openPlacesModal(+td.dataset.i);
  });
  function tipText(idx){
    const u = renderedRows[idx]; if(!u) return '';
    const info = placesInfo(u, renderedIsUnit);
    const first = info.names.slice(0,5);
    let t = first.join('\n');
    const more = info.count - first.length;
    if(more>0) t += (t?'\n':'') + `+ ${nf.format(more)} place(s)`;
    if(!info.names.length) t = `${nf.format(info.count)} place(s) · cliquer pour la liste`;
    else t += `\n— cliquer pour tout voir`;
    return t;
  }
  document.getElementById('e_rank_tb').addEventListener('mouseover', e=>{
    const td = e.target.closest('.pcell'); if(!td) return;
    tipEl.textContent = tipText(+td.dataset.i); tipEl.hidden = false;
  });
  document.getElementById('e_rank_tb').addEventListener('mousemove', e=>{
    if(tipEl.hidden) return;
    const pad=14, w=tipEl.offsetWidth, h=tipEl.offsetHeight;
    let x=e.clientX+pad, y=e.clientY+pad;
    if(x+w>innerWidth) x=e.clientX-pad-w;
    if(y+h>innerHeight) y=e.clientY-pad-h;
    tipEl.style.left=x+'px'; tipEl.style.top=y+'px';
  });
  document.getElementById('e_rank_tb').addEventListener('mouseout', e=>{
    if(e.target.closest('.pcell')) tipEl.hidden = true;
  });

  function renderRank(){
    const cid = sel.value, gran = cid ? gsel.value : '';
    renderedIsUnit = !!gran;
    const q = document.getElementById('e_q').value.toLowerCase();
    document.getElementById('e_q').placeholder = gran ? 'Rechercher une unité…' : 'Rechercher un utilisateur…';
    sliderWrap.style.display = gran ? 'none' : '';
    document.getElementById('e_rank_h2').textContent = gran
      ? `Classement E-réputation — ${LEVEL_LABELS[gran]||gran} · ${PLBL}`
      : `Classement E-réputation — utilisateurs · ${PLBL}`;

    const COLS = gran ? RCOLS_UNIT.filter(c => !(gran==='place' && c.k==='place_count')).map(c=>{
      if(!IS_DEFAULT && c.k==='connected_users') return {...c, t:'Connectés (période)'};
      if(!IS_DEFAULT && c.k==='rate') return {...c, t:'Taux (période)'};
      return c;
    }) : RCOLS_USER;
    if(!COLS.some(c=>c.k===sortK)) sortK = 'insight_actions';

    const maxP = +slider.value;
    let rows;
    if(!gran){
      rows = USER_ROWS.filter(u=>u.insight_actions>0)
        .filter(u=>!q || u.username.toLowerCase().includes(q) || (u.customer_name||'').toLowerCase().includes(q))
        .filter(u=> maxP>=10 || (u.n_admin_places||0) <= maxP);
    } else {
      rows = periodUnitRows(cid, gran)
        .filter(u=>!q || (u.unit_name||'').toLowerCase().includes(q));
    }
    rows = rows.slice().sort(cmp);
    renderedRows = rows;

    document.getElementById('e_rank_h').innerHTML = COLS.map(c=>`<th data-k="${c.k}">${c.t}</th>`).join('');
    bindRankSort();
    document.getElementById('e_rank_tb').innerHTML =
      rows.slice(0,500).map((u,i)=>'<tr>'+COLS.map(c=>cell(u,c,i)).join('')+'</tr>').join('');
    document.querySelectorAll('#e_rank_h th').forEach(th=>{
      th.classList.toggle('sorted',th.dataset.k===sortK);
      th.classList.toggle('asc',th.dataset.k===sortK&&sortAsc);});
    const slFoot = (!gran && maxP<10) ? ` · filtre : ≤ ${slider.value} place(s)` : '';
    const denomNote = (gran && !IS_DEFAULT) ? ' · connectés recalculés sur la période' : '';
    const placeNote = (gran==='place') ? ' · regroupement par nom d’établissement (deux fiches homonymes chez un même compte comptent comme une seule ligne)' : '';
    document.getElementById('e_rank_foot').textContent = gran
      ? `${rows.length} ${LEVEL_LABELS[gran]||gran} · classement exhaustif${denomNote}${placeNote}` + (rows.length>500?' (500 affichées)':'')
      : `${rows.length} utilisateur(s) actif(s) E-réputation sur la période` + slFoot + (rows.length>500?' (500 affichés)':'');
  }

  function applyFilters(f){
    if(f.customer !== undefined){
      const has = [...sel.options].some(o=>o.value===f.customer);
      sel.value = has ? f.customer : '';
    }
    if(f.period){ perSel.value = f.period; document.getElementById('e_custom_wrap').hidden = perSel.value!=='custom'; }
    if(f.from) fromEl.value = f.from;
    if(f.to) toEl.value = f.to;
    const cid = sel.value;
    usel.populate(cid, PERIMETERS);
    usel.disabled = !cid;
    if(cid && f.perim && f.perim.length) usel.setValues(f.perim);
    if(cid && !usel.values.length && f.gran) gsel.value = f.gran;
    render();
  }
  registerFilterSync('erep', applyFilters);
  applyFilters(SHARED_FILTERS);
}


/* ======================================================= INBOX (lazy) */
function initInbox(){
  const INBOX = window.__INBOX__ || {};
  const custs = INBOX.customers.slice().sort((a,b)=>b.connected_users-a.connected_users);
  const USERS30D = INBOX.users30d || [];
  const UNITS = INBOX.units || [];
  const USER_UNITS = INBOX.user_units || {};
  const PERIMETERS = INBOX.perimeters || [];
  // dénominateurs "connectés" par période — index : 0=30j, 1=mois préc., 2=trimestre, 3=année
  const CONN_PERIOD = INBOX.connected_period || {};
  const CONN_PERIOD_UNIT = (() => {
    const m = new Map();
    for(const r of (INBOX.connected_period_unit || [])) m.set(r[0] + '|' + r[1], [r[2], r[3], r[4], r[5]]);
    return m;
  })();
  const PERIOD_IDX = {'30d':0, 'prevmonth':1, 'quarter':2, 'year':3};
  // Inbox : tout le bloc Adoption est sur une fenêtre fixe de 30 j (le fait
  // user x jour fait 4,1 M de lignes, non embarquable côté client). Le dénominateur
  // reste donc sur 30 j lui aussi — numérateur et dénominateur restent cohérents,
  // et les libellés l'indiquent explicitement.
  function connIdx(){ return 0; }
  const CUSTOMER_DAY = INBOX.customer_day || [];
  const UDIM = INBOX.user_dim || {};
  const USER_PLACES = INBOX.user_places || {};
  const ACTIVITY_BREAKDOWN = INBOX.user_activity_breakdown || {};
  const CULTURE = INBOX.culture_place_snapshot || [];
  const SAL_IDX = {place:0,zone:1,sector:2,subtype:3,region:4,department:5,country:6,type:7,brand:8};
  const DATA_MAX = INBOX.data_max || new Date().toISOString().slice(0,10);
  const DATA_MIN = INBOX.data_min || DATA_MAX;
  const LEVEL_LABELS = {place:'places',zone:'zones',sector:'secteurs',subtype:'sous-types',
    region:'régions',department:'départements',country:'pays',type:'types',brand:'brand levels'};
  const LEVEL_SING = {place:'Place',zone:'Zone',sector:'Secteur',subtype:'Sous-type',
    region:'Région',department:'Département',country:'Pays',type:'Type',brand:'Brand level'};
  const PLABELS = {'30d':'30 derniers jours','prevmonth':'mois précédent','quarter':'trimestre actuel',
    'year':'année courante','custom':'période custom'};
  const MS = '(accès multi-strates)';

  const sel = document.getElementById('x_customer');
  const gsel = document.getElementById('x_gran');
  const usel = makePerim('x', () => { syncFilters('inbox', {perim: usel.values}); render(); }, LEVEL_SING);
  const perSel = document.getElementById('x_period');
  const fromEl = document.getElementById('x_from'), toEl = document.getElementById('x_to');
  const slider = document.getElementById('x_places');
  const sliderWrap = document.getElementById('x_slider_wrap');
  const tipEl = document.getElementById('x_tip');

  sel.add(new Option(`Tous les comptes (${custs.length})`, ''));
  custs.slice().sort((a,b)=>a.customer_name.localeCompare(b.customer_name)).forEach(c=>sel.add(new Option(`${c.customer_name} — ${nf.format(c.active_inbox_users)} actifs (30 j)`, c.customer_id)));
  fromEl.min = toEl.min = DATA_MIN; fromEl.max = toEl.max = DATA_MAX;
  fromEl.value = DATA_MIN; toEl.value = DATA_MAX;

  sel.onchange = () => { syncFilters('inbox', {customer: sel.value, perim: [], gran: ''}); render(); };
  gsel.onchange = () => { syncFilters('inbox', {gran: gsel.value}); render(); };
  perSel.onchange = ()=>{ document.getElementById('x_custom_wrap').hidden = perSel.value!=='custom'; syncFilters('inbox', {period: perSel.value}); render(); };
  fromEl.oninput = toEl.oninput = ()=>{ syncFilters('inbox', {from: fromEl.value, to: toEl.value}); render(); };
  document.getElementById('x_q').oninput = renderRank;
  slider.oninput = ()=>{ document.getElementById('x_places_val').textContent = slider.value==='10'?'10+':slider.value; renderRank(); };

  document.getElementById('x_disclaimer').textContent =
    "Funnel Inbox affiné (2026-09-16) : « Connecté Inbox » = a consulté l'inbox, sans forcément agir (l'inbox est souvent la page d'accueil, donc déjà un signal d'engagement en soi). « Actif Inbox » = a effectué au moins une action (envoyé ≥ 1 réponse). "
    + "Ces 2 signaux viennent de sources de tracking distinctes (consultation vs réponse) : « Actif » n'est donc pas toujours un sous-ensemble strict de « Connecté » — une minorité d'utilisateurs répondent sans qu'un événement de consultation Inbox soit enregistré ce jour-là. Effet marginal (599 utilisateurs sur 24 488 actifs, tous comptes) mais localement plus visible sur 2 comptes (Chaussea, Feu Vert : jusqu'à ~18 % des actifs de ces comptes), où « Actif » peut dépasser « Connecté ». "
    + "Cette distinction connecté/actif est spécifique à l'Inbox (jugée peu pertinente pour Insight/E-réputation, laissés inchangés). Le Top adopters/drop-off et le classement par niveau utilisent désormais aussi cette définition (classés par réponses, pas par simple consultation). "
    + "KPI, top adopters/drop-off, classement et Value Driver sont figés sur une fenêtre de 30 jours glissants (comme les dénominateurs « connectés » ailleurs dans le dashboard) — seule la courbe d'évolution ci-dessous suit le sélecteur de période. "
    + "Granularité réglable quand un compte est sélectionné : rattachement hiérarchique (comme le filtre Périmètre) — un utilisateur compte dans une unité s'il l'administre directement OU si l'un de ses magasins administrés en dépend (entre 1 et 60 magasins administrés ; au-delà, profil siège/national exclu du classement par niveau). Un utilisateur peut appartenir à plusieurs unités du même niveau (ex. administre 2 régions) — la somme des « Connectés » sur toutes les lignes d'un niveau peut donc dépasser le total du compte — en général de quelques pourcents, mais jusqu'à +50 % sur les comptes très maillés (mesuré : Unibail au niveau Pays, 191 contre 126). Comparez donc les unités entre elles plutôt que de sommer les lignes. "
    + "Value Driver Culture Client : note de relation client = ENGAGEMENT_SCORE (figée le 5 du mois pour le mois échu) ; taux/temps de réponse et volume en attente = MONTHLY_PLACE_CHECKUPS (snapshot du dernier mois clos, évolution vs mois précédent). "
    + "KPI écartés pour le moment : % traité en moins de 72h, activation des notifications (pas de signal identifié à ce jour).";

  let sortK='n_inbox', sortAsc=false;
  let USER_ROWS=[], renderedRows=[], renderedIsUnit=false;
  let PERIOD=['',''], PLBL='', IS_DEFAULT=true;

  /* ---------- période (courbe uniquement) ---------- */
  function periodRange(){
    const iso = dt => dt.toISOString().slice(0,10);
    const emax = new Date(DATA_MAX + 'T00:00:00Z');
    const p = perSel.value;
    if(p === 'custom') return [fromEl.value || DATA_MIN, toEl.value || DATA_MAX];
    if(p === 'prevmonth'){
      const y=emax.getUTCFullYear(), m=emax.getUTCMonth();
      return [iso(new Date(Date.UTC(y, m-1, 1))), iso(new Date(Date.UTC(y, m, 0)))];
    }
    if(p === 'quarter'){
      const y=emax.getUTCFullYear(), q=Math.floor(emax.getUTCMonth()/3);
      return [iso(new Date(Date.UTC(y, q*3, 1))), DATA_MAX];
    }
    if(p === 'year') return [iso(new Date(Date.UTC(emax.getUTCFullYear(), 0, 1))), DATA_MAX];
    const s = new Date(emax); s.setUTCDate(s.getUTCDate() - 29);
    return [iso(s), DATA_MAX];
  }

  function periodDaily(start, end, cid){
    const byDay = new Map();
    for(const r of CUSTOMER_DAY){
      if(r.d < start || r.d > end) continue;
      if(cid && r.k !== cid) continue;
      let o = byDay.get(r.d);
      if(!o){ o = {d:r.d, au:0, rp:0}; byDay.set(r.d, o); }
      o.au += r.au||0; o.rp += r.rp||0;
    }
    return [...byDay.values()].sort((a,b)=> a.d < b.d ? -1 : 1)
      .map(o=>({d:o.d, active_users:o.au, repliers_users:o.rp}));
  }

  function connFor(cid){
    // Le dénominateur suit la période choisie (corrigé 2026-09-17) : auparavant il
    // restait figé à 30 j pendant que le numérateur "actifs" suivait la période,
    // ce qui gonflait le ratio (et le faisait dépasser 100 % sur certains comptes).
    // Période "custom" : non précalculable -> null, le ratio est alors masqué.
    const pi = connIdx();
    if(pi === undefined) return null;
    const cs = cid ? custs.filter(c=>c.customer_id===cid) : custs;
    return cs.reduce((s,c)=>{
      const a = CONN_PERIOD[c.customer_id];
      return s + (a ? (a[pi] || 0) : 0);
    }, 0);
  }
  function connForUnits(cid, tokens){
    const pi = connIdx();
    if(pi === undefined) return null;
    let s = 0;
    for(const t of tokens){
      const a = CONN_PERIOD_UNIT.get(cid + '|' + t);
      if(a) s += a[pi] || 0;
    }
    return s;
  }
  function ctxLabel(cid){
    const cs = cid ? custs.filter(c=>c.customer_id===cid) : custs;
    return cid ? (cs[0] ? cs[0].customer_name : '—') : `${cs.length} comptes`;
  }
  function rosterFor(cid){
    const cs = cid ? custs.filter(c=>c.customer_id===cid) : custs;
    return cs.reduce((s,c)=>s+(c.roster||0), 0);
  }

  function userRowsFor(cid){
    const rows = cid ? USERS30D.filter(u=>u.customer_id===cid) : USERS30D;
    return rows.map(u=>{
      const key = u.username + '|' + u.customer_id;
      const d = UDIM[key] || {};
      return {key, username:u.username, customer_id:u.customer_id, customer_name:u.customer_name || '—',
        role: u.role || '', n_admin_places: u.n_admin_places || 0, sal: d.sal || [],
        n_inbox: u.n_inbox||0, n_mobile: u.n_mobile||0,
        n_replies: u.n_replies||0, n_replies_ai: u.n_replies_ai||0, n_replies_templated: u.n_replies_templated||0,
        is_connected_inbox: !!u.is_connected_inbox, is_active_inbox: !!u.is_active_inbox};
    });
  }

  function unitsForLevel(u, gran){
    const toks = USER_UNITS[u.key];
    if(!toks || !toks.length) return [];
    const out = [];
    for(const t of toks){
      const sep = t.indexOf('\u0001');
      if(t.slice(0, sep) === gran) out.push(t.slice(sep + 1));
    }
    return out;
  }
  function unitRows(cid, gran){
    const byUnit = new Map();
    for(const u of USER_ROWS){
      const names = unitsForLevel(u, gran);
      for(const name of names){
        let o = byUnit.get(name);
        if(!o){ o = {ci:0, ai:0, ia:0, rp:0}; byUnit.set(name, o); }
        if(u.n_inbox > 0 || u.n_replies > 0) o.ci += 1;
        if(u.n_replies > 0) o.ai += 1;
        o.ia += u.n_inbox;
        o.rp += u.n_replies;
      }
    }
    return UNITS.filter(x=>x.customer_id===cid && x.level===gran).map(x=>{
      const p = byUnit.get(x.unit_name) || {ci:0, ai:0, ia:0, rp:0};
      return {unit_name:x.unit_name, place_count:x.place_count, place_names:x.place_names,
        connected_users:x.connected_users,
        connected_inbox_users:p.ci, active_inbox_users:p.ai,
        inbox_actions:p.ia, replies:p.rp,
        rate: p.ci ? p.ai / p.ci : 0};
    });
  }

  /* ---------- value driver · Culture Client ---------- */
  function gDeltaLbl(cur, prev, lbl, opts){
    opts = opts || {};
    const invert = !!opts.invert; // true = une baisse est positive (ex: messages en attente)
    if(prev != null && prev > 0){
      const d = (cur - prev) / prev;
      if(Math.abs(d) < 0.01) return `<span class="dlt flat">≈ stable <span class="muted">${lbl}</span></span>`;
      const good = invert ? d < 0 : d > 0;
      const cls = good ? 'up' : 'dn', arw = d > 0 ? '▲ ' : '▼ ';
      return `<span class="dlt ${cls}">${arw}${pct(Math.abs(d))} <span class="muted">${lbl}</span></span>`;
    }
    if(cur > 0 && prev === 0) return `<span class="dlt up">nouveau <span class="muted">${lbl}</span></span>`;
    return `<span class="dlt flat">— <span class="muted">${lbl}</span></span>`;
  }
  function placesForScope(cid, perimSel){
    let rows = cid ? CULTURE.filter(p=>p.c===cid) : CULTURE;
    if(cid && perimSel.length){
      const toks = perimSel.map(t=>{ const i=t.indexOf(''); return [t.slice(0,i), t.slice(i+1)]; });
      rows = rows.filter(p => toks.some(([lv,nm]) => p.u[SAL_IDX[lv]] === nm));
    }
    return rows;
  }
  function weightedBy(rows, key, weightKey){
    let num=0, den=0;
    for(const p of rows){ if(p[key]!=null && p[weightKey]){ num += p[key]*p[weightKey]; den += p[weightKey]; } }
    return den ? num/den : null;
  }
  function renderValueDriverCulture(cid, perimSel){
    const rows = placesForScope(cid, perimSel);
    const wt = k => weightedBy(rows, k, 'totc');
    const es = wt('es'), esM1 = wt('esm1'), esLy = wt('esly');
    const repc = rows.reduce((s,p)=>s+(p.repc||0),0), totc = rows.reduce((s,p)=>s+(p.totc||0),0);
    const rr = totc ? repc/totc : null, rrM1 = wt('rrm1');
    const SEC_PER_DAY = 86400;
    const rtimeRaw = weightedBy(rows, 'rtime', 'repc'), rtimeM1Raw = wt('rtimem1');
    const rtime = rtimeRaw!=null ? rtimeRaw/SEC_PER_DAY : null;
    const rtimeM1 = rtimeM1Raw!=null ? rtimeM1Raw/SEC_PER_DAY : null;
    const notr = rows.reduce((s,p)=>s+(p.notr||0),0), notrM1 = rows.reduce((s,p)=>s+(p.notrm1||0),0);

    const cards = [];
    cards.push(`<div class="kpi vd"><div class="lab">Note de relation client</div>
      <div class="val">${es!=null ? es.toFixed(2) : '—'} <span class="muted" style="font-size:13px">/5</span></div>
      <div class="sub2">ENGAGEMENT_SCORE, dernier mois clos · ${esLy!=null ? 'vs ' + esLy.toFixed(2) + ' il y a 12 mois' : 'pas de comparatif N-1'}</div>
      ${gDeltaLbl(es, esM1, 'vs mois précédent')}</div>`);
    cards.push(`<div class="kpi vd"><div class="lab">Taux de réponse</div>
      <div class="val">${rr!=null ? pct(rr) : '—'}</div>
      <div class="sub2">${nf.format(repc)} / ${nf.format(totc)} conversations répondues (dernier mois clos)</div>
      ${gDeltaLbl(rr, rrM1, 'vs mois précédent')}</div>`);
    cards.push(`<div class="kpi vd"><div class="lab">Temps de réponse moyen</div>
      <div class="val">${rtime!=null ? r2(rtime) : '—'} <span class="muted" style="font-size:13px">j</span></div>
      <div class="sub2">délai moyen conversation → réponse, dernier mois clos</div>
      ${gDeltaLbl(rtime, rtimeM1, 'vs mois précédent', {invert:true})}</div>`);
    cards.push(`<div class="kpi vd"><div class="lab">Messages en attente</div>
      <div class="val">${nf.format(notr)}</div>
      <div class="sub2">conversations non répondues, snapshot fin de mois</div>
      ${gDeltaLbl(notr, notrM1, 'vs mois précédent', {invert:true})}</div>`);

    const ur = cid ? USER_ROWS : USER_ROWS; // déjà scopé compte + périmètre par render()
    const totReplies = ur.reduce((s,u)=>s+(u.n_replies||0),0);
    const totRepliesAi = ur.reduce((s,u)=>s+(u.n_replies_ai||0),0);
    const totRepliesTpl = ur.reduce((s,u)=>s+(u.n_replies_templated||0),0);
    const totInbox = ur.reduce((s,u)=>s+(u.n_inbox||0),0);
    const totMobile = ur.reduce((s,u)=>s+(u.n_mobile||0),0);

    // Nb de répondants = KPI "Actif Inbox" affiché en tête de section Adoption (même population) —
    // pas dupliqué ici pour éviter d'afficher deux fois le même chiffre.
    cards.push(`<div class="kpi vd"><div class="lab">Usage de l'IA de réponse</div>
      <div class="val">${totReplies ? pct(totRepliesAi/totReplies) : '—'}</div>
      <div class="sub2">${nf.format(totRepliesAi)} / ${nf.format(totReplies)} réponses assistées IA · 30 jours</div></div>`);
    cards.push(`<div class="kpi vd"><div class="lab">Usage des modèles de réponse</div>
      <div class="val">${totReplies ? pct(totRepliesTpl/totReplies) : '—'}</div>
      <div class="sub2">${nf.format(totRepliesTpl)} / ${nf.format(totReplies)} réponses via un modèle · 30 jours</div></div>`);
    cards.push(`<div class="kpi vd"><div class="lab">Usage de l'application mobile</div>
      <div class="val">${totInbox ? pct(totMobile/totInbox) : '—'}</div>
      <div class="sub2">${nf.format(totMobile)} / ${nf.format(totInbox)} actions Inbox faites sur mobile · 30 jours</div></div>`);

    document.getElementById('x_vd').innerHTML = cards.join('');
    document.getElementById('x_vd_foot').textContent =
      `Note de relation client, taux/temps de réponse et messages en attente : moyenne/somme pondérée par le volume de conversations des établissements du périmètre, dernier mois clos vs mois précédent. `
      + `IA/modèles/mobile : calculés sur les 30 derniers jours glissants, sans comparatif période précédente (non disponible à cette granularité). `
      + `Le nombre de répondants (« Actif Inbox ») est affiché en tête de la section Adoption ci-dessus. `
      + `KPI écartés pour le moment : % traité en <72h, activation des notifications.`;
  }

  /* ---------- render principal ---------- */
  function render(){
    const cid = sel.value;
    if(usel.dataset.cid !== (cid||'')) usel.populate(cid, PERIMETERS);
    usel.disabled = !cid;
    PERIOD = periodRange();
    IS_DEFAULT = perSel.value === '30d';
    PLBL = PLABELS[perSel.value];
    document.getElementById('x_custom_wrap').hidden = perSel.value !== 'custom';
    document.getElementById('x_period_dates').textContent = IS_DEFAULT
      ? 'fenêtre glissante' : `${PERIOD[0]} → ${PERIOD[1]}`;
    const pTag = IS_DEFAULT ? '30 jours' : PLBL;
    document.getElementById('x_chart_h').textContent = `Connectés & actifs Inbox — quotidien · ${pTag}`;

    USER_ROWS = userRowsFor(cid);
    const perimSel = cid ? usel.values : [];
    let unitScope = null;
    if(perimSel.length){
      const pset = new Set(perimSel);
      USER_ROWS = USER_ROWS.filter(u => (USER_UNITS[u.key]||[]).some(t=>pset.has(t)));
      const prows = PERIMETERS.filter(p=>p.customer_id===cid && pset.has(p.level+''+p.unit_name));
      unitScope = { rows: prows, label: perimSel.length===1
        ? LEVEL_SING[perimSel[0].split('')[0]] + ' « ' + perimSel[0].split('')[1] + ' »'
        : perimSel.length + ' unités' };
    }
    const scopeP = unitScope ? {
      connected_users: connForUnits(cid, perimSel),
    } : null;
    const connectedInbox = USER_ROWS.filter(u=>u.is_connected_inbox).length;
    const activeInbox = USER_ROWS.filter(u=>u.is_active_inbox).length;
    const totalReplies = USER_ROWS.reduce((s,u)=>s+(u.n_replies||0),0);
    const connected = scopeP ? (scopeP.connected_users || 0) : connFor(cid);

    document.getElementById('x_ctx').textContent =
      (cid ? `${ctxLabel(cid)} · ${nf.format(rosterFor(cid))} comptes créés · ` : `${ctxLabel(cid)} · `)
      + `${nf.format(connected)} connectés (30 j)`
      + (unitScope ? ` · périmètre : ${unitScope.label}` + (perimSel.length>1 ? ' (connectés = somme des unités)' : '') : '');

    const kpis = [
      ['Connecté Inbox', connectedInbox, connected ? pct(connectedInbox/connected) : null, 'des connectés (30 j)'],
      ['Actif Inbox', activeInbox, connectedInbox ? pct(activeInbox/connectedInbox) : null, 'des connectés Inbox'],
      ['Réponses', totalReplies, activeInbox ? (totalReplies/activeInbox).toFixed(1) : null, 'réponse(s)/actif Inbox'],
    ];
    document.getElementById('x_kpis').innerHTML = kpis.map(([l,v,r,d])=>`
      <div class="kpi"><div class="lab">${l}</div><div class="val">${nf.format(v)}</div>
      <div class="rat">${r!=null ? r+' '+d : (d || '&nbsp;')}</div></div>`).join('');

    lineChart('x_chart', periodDaily(PERIOD[0], PERIOD[1], cid),
      [['active_users','#6cc79a','Connectés Inbox'],['repliers_users','#3a7bd5','Actifs Inbox']], 'd');

    if(!cid){
      gsel.value=''; gsel.disabled=true;
      document.getElementById('x_gran_hint').textContent = 'Sélectionnez un compte pour filtrer par niveau ou périmètre.';
    } else {
      gsel.disabled = perimSel.length>0;
      if(perimSel.length) gsel.value='';
      document.getElementById('x_gran_hint').textContent = perimSel.length ? 'Périmètre actif → agrégation par niveau désactivée.' : '';
    }

    renderValueDriverCulture(cid, perimSel);
    renderTopDrop(cid, Math.max(connectedInbox - activeInbox, 0));
    renderRank();
  }

  function renderTopDrop(cid, zero){
    const gran = cid ? gsel.value : '';
    const topH = document.getElementById('x_top_h'), dropH = document.getElementById('x_drop_h');

    if(!gran){
      topH.textContent = `Top adopters — utilisateurs · 30 jours`;
      dropH.textContent = `Adoption drop-off — utilisateurs · 30 jours`;
      const withA = USER_ROWS.filter(u=>u.n_replies>0);
      const desc = withA.slice().sort((a,b)=> b.n_replies-a.n_replies || (a.username<b.username?-1:1));
      const asc  = withA.slice().sort((a,b)=> a.n_replies-b.n_replies || (a.username<b.username?-1:1));
      const li = u=>`<li>${u.username} <span class="muted">— ${u.customer_name}</span> <span class="n">${nf.format(u.n_replies)} réponses</span></li>`;
      document.getElementById('x_top').innerHTML  = desc.slice(0,3).map(li).join('') || '<li class="muted">Aucun utilisateur actif</li>';
      document.getElementById('x_drop').innerHTML = asc.slice(0,3).map(li).join('')  || '<li class="muted">Aucun utilisateur actif</li>';
      document.getElementById('x_drop_foot').textContent =
        zero>0 ? `+ ${nf.format(zero)} connecté(s) Inbox (30 j) sans réponse sur la période (non listés).` : '';
      return;
    }

    const lbl = LEVEL_LABELS[gran] || gran;
    topH.textContent = `Top adopters — ${lbl} · 30 jours`;
    dropH.textContent = `Adoption drop-off — ${lbl} · 30 jours`;
    const rows = unitRows(cid, gran);
    const asc = rows.slice().sort((a,b)=> a.active_inbox_users-b.active_inbox_users
      || b.connected_inbox_users-a.connected_inbox_users || (a.unit_name<b.unit_name?-1:1));
    const desc = rows.slice().sort((a,b)=> b.active_inbox_users-a.active_inbox_users
      || b.replies-a.replies || (a.unit_name<b.unit_name?-1:1));
    const rate = u => u.connected_inbox_users ? pct(u.active_inbox_users/u.connected_inbox_users) : '—';
    const li = u => `<li>${u.unit_name}`
      + ` <span class="muted">— ${nf.format(u.active_inbox_users)}/${nf.format(u.connected_inbox_users)} actifs·connectés Inbox (30 j) · ${rate(u)} d'adoption ·</span>`
      + ` <span class="n">${nf.format(u.replies)} réponses</span></li>`;
    document.getElementById('x_top').innerHTML  = desc.filter(u=>u.active_inbox_users>0).slice(0,3).map(li).join('') || '<li class="muted">Aucune unité avec réponse Inbox</li>';
    document.getElementById('x_drop').innerHTML = asc.slice(0,3).map(li).join('') || '<li class="muted">Aucune unité à ce niveau</li>';
    document.getElementById('x_drop_foot').textContent =
      `${rows.length} ${lbl} avec ≥ 1 connecté Inbox (30 j) · le drop-off inclut les unités à 0 réponse sur la période.`;
  }

  /* ---------- classement (tableau) ---------- */
  const RCOLS_USER=[
    {k:'username',t:'Utilisateur',kind:'txt',name:true},
    {k:'customer_name',t:'Compte',kind:'txt'},
    {k:'role',t:'Rôle',kind:'txt'},
    {k:'n_admin_places',t:'Places',kind:'places'},
    {k:'n_inbox',t:'Consultations',kind:'actions'},
    {k:'n_replies',t:'Réponses',kind:'num'},
    {k:'n_replies_ai',t:'dont IA',kind:'num'},
    {k:'n_mobile',t:'dont mobile',kind:'num'},
  ];
  const RCOLS_UNIT=[
    {k:'unit_name',t:'Unité',kind:'txt',name:true},
    {k:'place_count',t:'Places',kind:'places'},
    {k:'connected_users',t:'Connectés',kind:'num'},
    {k:'connected_inbox_users',t:'Connectés Inbox',kind:'num'},
    {k:'active_inbox_users',t:'Actifs Inbox',kind:'num'},
    {k:'rate',t:'Taux d’adoption',kind:'pct'},
    {k:'inbox_actions',t:'Consultations',kind:'actions'},
    {k:'replies',t:'Réponses',kind:'num'},
  ];

  function placesInfo(u, isUnit){
    if(isUnit){
      const c = u.place_count;
      return {count: (c==null? null : c), names: u.place_names || [], label: u.unit_name};
    }
    const p = USER_PLACES[`${u.username}|${u.customer_id}`] || {total: u.n_admin_places||0, names: []};
    return {count: p.total, names: p.names || [], label: u.username};
  }
  function activityInfo(u, isUnit){
    if(!isUnit){
      const bd = ACTIVITY_BREAKDOWN[u.key] || [];
      return {total: u.n_inbox||0, breakdown: bd, label: u.username};
    }
    // vue unité : somme du détail de tous les utilisateurs rattachés à cette unité (option B)
    const gran = gsel.value;
    const agg = new Map();
    for(const usr of USER_ROWS){
      if(!unitsForLevel(usr, gran).includes(u.unit_name)) continue;
      for(const [act, n] of (ACTIVITY_BREAKDOWN[usr.key] || [])) agg.set(act, (agg.get(act)||0) + n);
    }
    return {total: u.inbox_actions||0, breakdown: [...agg.entries()], label: u.unit_name};
  }
  function bindRankSort(){
    document.querySelectorAll('#x_rank_h th').forEach(th=>th.onclick=()=>{
      const k=th.dataset.k; sortAsc=(k===sortK)?!sortAsc:false; sortK=k; renderRank();
    });
  }
  function cmp(a,b){
    let x=a[sortK],y=b[sortK];
    if(typeof x==='string'||typeof y==='string'){x=(x||'')+'';y=(y||'')+'';return sortAsc?x.localeCompare(y):y.localeCompare(x);}
    return sortAsc?(x||0)-(y||0):(y||0)-(x||0);
  }
  function cell(u,c,idx){
    if(c.kind==='txt') return `<td style="text-align:left"${c.name?' class="name"':' class="muted"'}>${u[c.k]||'—'}</td>`;
    if(c.kind==='pct') return `<td>${u.connected_inbox_users?pct(u[c.k]||0):'—'}</td>`;
    if(c.kind==='places'){
      const info = placesInfo(u, renderedIsUnit);
      if(info.count==null) return `<td class="muted">—</td>`;
      return `<td class="pcell" data-i="${idx}">${nf.format(info.count)}</td>`;
    }
    if(c.kind==='actions') return `<td class="acell" data-i="${idx}">${nf.format(u[c.k]||0)}</td>`;
    return `<td>${nf.format(u[c.k]||0)}</td>`;
  }

  function openPlacesModal(idx){
    const u = renderedRows[idx]; if(!u) return;
    const info = placesInfo(u, renderedIsUnit);
    const shown = info.names.length, more = info.count - shown;
    const cappedByExport = shown >= 10;
    const moreNote = !more ? '' : cappedByExport
      ? `+ ${nf.format(more)} place(s) non listée(s) (limite d'export : 10 noms).`
      : `+ ${nf.format(more)} place(s) non affichée(s) : plusieurs établissements de ce compte partagent le même nom (comptés une seule fois dans la liste).`;
    document.getElementById('x_modal').innerHTML =
      `<div class="modal-bg"><div class="modal">
         <h3>Places — ${info.label}</h3>
         <div class="sub2">${nf.format(info.count)} place(s)${more>0?` · ${nf.format(shown)} affichées`:''}</div>
         <ul>${info.names.map(n=>`<li>${n}</li>`).join('') || '<li class="muted">Noms non disponibles</li>'}</ul>
         ${more>0?`<div class="sub2" style="margin-top:8px">${moreNote}</div>`:''}
         <button id="x_modal_close">Fermer</button>
       </div></div>`;
    document.getElementById('x_modal').hidden = false;
  }
  function closeModal(){ const m=document.getElementById('x_modal'); m.hidden=true; m.innerHTML=''; }
  document.getElementById('x_modal').addEventListener('click', e=>{
    if(e.target.id==='x_modal' || e.target.classList.contains('modal-bg') || e.target.id==='x_modal_close') closeModal();
  });
  document.addEventListener('keydown', e=>{ if(e.key==='Escape') closeModal(); });
  document.getElementById('x_rank_tb').addEventListener('click', e=>{
    const tdp = e.target.closest('.pcell'); if(tdp){ openPlacesModal(+tdp.dataset.i); return; }
    const tda = e.target.closest('.acell'); if(tda){ openActionsModal(+tda.dataset.i); return; }
  });
  function openActionsModal(idx){
    const u = renderedRows[idx]; if(!u) return;
    const info = activityInfo(u, renderedIsUnit);
    const bd = info.breakdown.slice().sort((a,b)=>b[1]-a[1]);
    document.getElementById('x_modal').innerHTML =
      `<div class="modal-bg"><div class="modal">
         <h3>Consultations Inbox — ${info.label}</h3>
         <div class="sub2">${nf.format(info.total)} consultation(s) sur 30 jours, par type d'activité</div>
         <ul>${bd.map(([act,n])=>`<li>${act} — ${nf.format(n)}</li>`).join('') || '<li class="muted">Détail non disponible</li>'}</ul>
         <button id="x_modal_close">Fermer</button>
       </div></div>`;
    document.getElementById('x_modal').hidden = false;
  }
  function tipText(idx){
    const u = renderedRows[idx]; if(!u) return '';
    const info = placesInfo(u, renderedIsUnit);
    const first = info.names.slice(0,5);
    let t = first.join('\n');
    const more = info.count - first.length;
    if(more>0) t += (t?'\n':'') + `+ ${nf.format(more)} place(s)`;
    if(!info.names.length) t = `${nf.format(info.count)} place(s) · cliquer pour la liste`;
    else t += `\n— cliquer pour tout voir`;
    return t;
  }
  function tipTextActions(idx){
    const u = renderedRows[idx]; if(!u) return '';
    const info = activityInfo(u, renderedIsUnit);
    const bd = info.breakdown.slice().sort((a,b)=>b[1]-a[1]);
    const first = bd.slice(0,5).map(([act,n])=>`${act} — ${nf.format(n)}`);
    let t = first.join('\n');
    if(!bd.length) t = `${nf.format(info.total)} consultation(s) · cliquer pour le détail`;
    else t += `\n— cliquer pour tout voir`;
    return t;
  }
  document.getElementById('x_rank_tb').addEventListener('mouseover', e=>{
    const tdp = e.target.closest('.pcell');
    if(tdp){ tipEl.textContent = tipText(+tdp.dataset.i); tipEl.hidden = false; return; }
    const tda = e.target.closest('.acell');
    if(tda){ tipEl.textContent = tipTextActions(+tda.dataset.i); tipEl.hidden = false; return; }
  });
  document.getElementById('x_rank_tb').addEventListener('mousemove', e=>{
    if(tipEl.hidden) return;
    const pad=14, w=tipEl.offsetWidth, h=tipEl.offsetHeight;
    let x=e.clientX+pad, y=e.clientY+pad;
    if(x+w>innerWidth) x=e.clientX-pad-w;
    if(y+h>innerHeight) y=e.clientY-pad-h;
    tipEl.style.left=x+'px'; tipEl.style.top=y+'px';
  });
  document.getElementById('x_rank_tb').addEventListener('mouseout', e=>{
    if(e.target.closest('.pcell') || e.target.closest('.acell')) tipEl.hidden = true;
  });

  function renderRank(){
    const cid = sel.value, gran = cid ? gsel.value : '';
    renderedIsUnit = !!gran;
    const q = document.getElementById('x_q').value.toLowerCase();
    document.getElementById('x_q').placeholder = gran ? 'Rechercher une unité…' : 'Rechercher un utilisateur…';
    sliderWrap.style.display = gran ? 'none' : '';
    document.getElementById('x_rank_h2').textContent = gran
      ? `Classement d'adoption — ${LEVEL_LABELS[gran]||gran} · 30 jours`
      : `Classement d'adoption — utilisateurs · 30 jours`;

    const COLS = gran ? RCOLS_UNIT.filter(c => !(gran==='place' && c.k==='place_count')) : RCOLS_USER;
    if(!COLS.some(c=>c.k===sortK)) sortK = gran ? 'inbox_actions' : 'n_inbox';

    const maxP = +slider.value;
    let rows;
    if(!gran){
      rows = USER_ROWS.filter(u=>u.n_inbox>0 || u.n_replies>0)
        .filter(u=>!q || u.username.toLowerCase().includes(q) || (u.customer_name||'').toLowerCase().includes(q))
        .filter(u=> maxP>=10 || (u.n_admin_places||0) <= maxP);
    } else {
      rows = unitRows(cid, gran)
        .filter(u=>!q || (u.unit_name||'').toLowerCase().includes(q));
    }
    rows = rows.slice().sort(cmp);
    renderedRows = rows;

    document.getElementById('x_rank_h').innerHTML = COLS.map(c=>`<th data-k="${c.k}">${c.t}</th>`).join('');
    bindRankSort();
    document.getElementById('x_rank_tb').innerHTML =
      rows.slice(0,500).map((u,i)=>'<tr>'+COLS.map(c=>cell(u,c,i)).join('')+'</tr>').join('');
    document.querySelectorAll('#x_rank_h th').forEach(th=>{
      th.classList.toggle('sorted',th.dataset.k===sortK);
      th.classList.toggle('asc',th.dataset.k===sortK&&sortAsc);});
    const slFoot = (!gran && maxP<10) ? ` · filtre : ≤ ${slider.value} place(s)` : '';
    const placeNote = (gran==='place') ? ' · regroupement par nom d’établissement (deux fiches homonymes chez un même compte comptent comme une seule ligne)' : '';
    document.getElementById('x_rank_foot').textContent = gran
      ? `${rows.length} ${LEVEL_LABELS[gran]||gran} · classement exhaustif${placeNote}` + (rows.length>500?' (500 affichées)':'')
      : `${rows.length} utilisateur(s) avec action Inbox sur les 30 derniers jours` + slFoot + (rows.length>500?' (500 affichés)':'');
  }

  function applyFilters(f){
    if(f.customer !== undefined){
      const has = [...sel.options].some(o=>o.value===f.customer);
      sel.value = has ? f.customer : '';
    }
    if(f.period){ perSel.value = f.period; document.getElementById('x_custom_wrap').hidden = perSel.value!=='custom'; }
    if(f.from) fromEl.value = f.from;
    if(f.to) toEl.value = f.to;
    const cid = sel.value;
    usel.populate(cid, PERIMETERS);
    usel.disabled = !cid;
    if(cid && f.perim && f.perim.length) usel.setValues(f.perim);
    if(cid && !usel.values.length && f.gran) gsel.value = f.gran;
    render();
  }
  registerFilterSync('inbox', applyFilters);
  applyFilters(SHARED_FILTERS);
}


/* ---------- widget Périmètre (multi-select + recherche) ---------- */
function makePerim(P, onChange, LSING){
  const g = s => document.getElementById(P + '_unit_' + s);
  const ms = g('ms'), btn = g('btn'), lbl = g('lbl'), pop = g('pop'), qin = g('q'), list = g('list'), clr = g('clear');
  const ORDER = ['region','zone','sector','subtype','department','country','type','brand','place'];
  const st = { values: [], all: [], disabled: true, dataset: {} };

  function draw(){
    const q = qin.value.trim().toLowerCase();
    const chosen = new Set(st.values);
    const byLvl = {};
    st.all.forEach(o => { if(!q || o.nm.toLowerCase().includes(q)) (byLvl[o.lv] = byLvl[o.lv] || []).push(o); });
    let h = '';
    ORDER.forEach(lv => {
      const arr = byLvl[lv]; if(!arr) return;
      h += '<div class="ms-grp">' + (LSING[lv] || lv) + '</div>';
      arr.forEach(o => {
        h += '<label class="ms-it"><input type="checkbox" value="' + o.tok.replace(/"/g,'&quot;') + '"'
          + (chosen.has(o.tok) ? ' checked' : '') + '>' + o.nm + '</label>';
      });
    });
    list.innerHTML = h || '<div class="ms-empty">Aucun résultat</div>';
    lbl.textContent = st.values.length === 0 ? 'Tout le compte'
      : (st.values.length === 1 ? st.values[0].split('\u0001')[1] : (st.values.length + ' unités'));
    ms.classList.toggle('has', st.values.length > 0);
  }

  list.addEventListener('change', e => {
    const cb = e.target.closest('input[type=checkbox]'); if(!cb) return;
    if(cb.checked) st.values.push(cb.value);
    else st.values = st.values.filter(v => v !== cb.value);
    draw(); onChange();
  });
  qin.addEventListener('input', draw);
  btn.addEventListener('click', () => {
    if(st.disabled) return;
    pop.hidden = !pop.hidden;
    if(!pop.hidden){ qin.value = ''; draw(); qin.focus(); }
  });
  clr.addEventListener('click', () => { st.values = []; draw(); onChange(); });
  document.addEventListener('click', e => { if(!ms.contains(e.target)) pop.hidden = true; });

  return {
    get values(){ return st.values.slice(); },
    get disabled(){ return st.disabled; },
    set disabled(v){ st.disabled = !!v; ms.classList.toggle('ms-off', !!v); if(v) pop.hidden = true; },
    dataset: st.dataset,
    populate(cid, perimeters){
      st.dataset.cid = cid || '';
      st.values = [];
      st.all = (cid ? perimeters.filter(p => p.customer_id === cid) : [])
        .map(p => ({ lv: p.level, nm: p.unit_name, tok: p.level + '\u0001' + p.unit_name }))
        .sort((a, b) => a.nm.localeCompare(b.nm));
      draw();
    },
    // restaure une sélection (synchro inter-onglets) — ignore les tokens
    // absents du compte courant (unités qui n'existent pas chez ce client).
    setValues(tokens){
      const known = new Set(st.all.map(o => o.tok));
      st.values = (tokens || []).filter(t => known.has(t));
      draw();
    },
  };
}

/* ---------- shared line chart ---------- */
function lineChart(elId, rows, series, xkey){
  const host = document.getElementById(elId);
  if(!rows.length){ host.innerHTML = '<div class="muted">Pas de données</div>'; return; }
  const W=1180, H=210, padL=8, padR=8, padT=14, padB=26;
  const n = rows.length;
  const nfl = new Intl.NumberFormat('fr-FR');
  const xs = i => padL + i*(W-padL-padR)/Math.max(n-1,1);
  const max = Math.max(1, ...rows.flatMap(r=>series.map(s=>r[s[0]]||0)));
  const ys = v => H-padB - v*(H-padB-padT)/max;
  const path = s => `<path fill="none" stroke="${s[1]}" stroke-width="1.6" d="${
    rows.map((r,i)=>(i?'L':'M')+xs(i).toFixed(1)+' '+ys(r[s[0]]||0).toFixed(1)).join(' ')}"/>`;

  // axe X : ~8 graduations réparties
  const nT = Math.min(8, n);
  const idxs = [...new Set(Array.from({length:nT}, (_,t)=> Math.round(t*(n-1)/Math.max(nT-1,1))))];
  const xticks = idxs.map(i=>{
    const anchor = i===0 ? 'start' : (i===n-1 ? 'end' : 'middle');
    return `<line x1="${xs(i).toFixed(1)}" y1="${H-padB}" x2="${xs(i).toFixed(1)}" y2="${H-padB+3}" stroke="var(--line)"/>`
      + `<text x="${xs(i).toFixed(1)}" y="${H-padB+14}" fill="var(--muted)" font-size="9" text-anchor="${anchor}">${rows[i][xkey]}</text>`;
  }).join('');
  // axe Y : max + milieu
  const yMid = Math.round(max/2);
  const yg = `<line x1="${padL}" y1="${ys(yMid).toFixed(1)}" x2="${W-padR}" y2="${ys(yMid).toFixed(1)}" stroke="var(--line)" stroke-dasharray="3 3"/>`
    + `<text x="${padL}" y="10" fill="var(--muted)" font-size="10">${nfl.format(max)}</text>`
    + `<text x="${padL}" y="${(ys(yMid)-3).toFixed(1)}" fill="var(--muted)" font-size="9">${nfl.format(yMid)}</text>`;

  host.innerHTML =
    `<div style="position:relative">
       <svg id="${elId}_svg" viewBox="0 0 ${W} ${H}" style="width:100%;height:auto;display:block">
         <line x1="${padL}" y1="${H-padB}" x2="${W-padR}" y2="${H-padB}" stroke="var(--line)"/>
         ${yg}${xticks}
         ${series.map(path).join('')}
         <line id="${elId}_gd" y1="${padT}" y2="${H-padB}" stroke="var(--muted)" stroke-width="1" style="opacity:0"/>
         <g id="${elId}_dt"></g>
         <rect id="${elId}_hit" x="0" y="0" width="${W}" height="${H}" fill="transparent" style="cursor:crosshair"/>
       </svg>
       <div id="${elId}_tt" style="position:absolute;pointer-events:none;display:none;z-index:5;
         background:var(--ink);color:var(--bg);font-size:11px;line-height:1.55;padding:6px 9px;
         border-radius:6px;white-space:nowrap;box-shadow:0 2px 12px rgba(0,0,0,.28)"></div>
     </div>`;

  const wrap = host.firstElementChild;
  const svg = document.getElementById(elId+'_svg');
  const hit = document.getElementById(elId+'_hit');
  const gd  = document.getElementById(elId+'_gd');
  const dt  = document.getElementById(elId+'_dt');
  const tt  = document.getElementById(elId+'_tt');

  hit.addEventListener('mousemove', evt=>{
    const rect = svg.getBoundingClientRect();
    const vx = (evt.clientX - rect.left) / rect.width * W;
    let i = Math.round((vx - padL) / ((W-padL-padR)/Math.max(n-1,1)));
    i = Math.max(0, Math.min(n-1, i));
    const r = rows[i], x = xs(i);
    gd.setAttribute('x1', x); gd.setAttribute('x2', x); gd.style.opacity = 1;
    dt.innerHTML = series.map(s=>`<circle cx="${x.toFixed(1)}" cy="${ys(r[s[0]]||0).toFixed(1)}" r="3.2" fill="${s[1]}" stroke="var(--panel)" stroke-width="1.5"/>`).join('');
    tt.innerHTML = `<b>${r[xkey]}</b>` + series.map(s=>
      `<br><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${s[1]};margin-right:5px"></span>`
      + `${s[2]||s[0]} : <b>${nfl.format(r[s[0]]||0)}</b>`).join('');
    tt.style.display = 'block';
    const wr = wrap.getBoundingClientRect();
    let left = evt.clientX - wr.left + 14;
    let top  = evt.clientY - wr.top + 12;
    if(left + tt.offsetWidth > wrap.clientWidth) left = evt.clientX - wr.left - tt.offsetWidth - 14;
    if(top + tt.offsetHeight > wrap.clientHeight) top = wrap.clientHeight - tt.offsetHeight - 4;
    tt.style.left = Math.max(0,left) + 'px';
    tt.style.top  = Math.max(0,top) + 'px';
  });
  hit.addEventListener('mouseleave', ()=>{ tt.style.display='none'; gd.style.opacity=0; dt.innerHTML=''; });
}
</script>
</body>
</html>
"""

import time as _t
VER = _t.strftime("%Y%m%d%H%M%S")

out = ROOT / "dashboard" / "index.html"
out.write_text(
    HTML.replace('<script src="data.js"></script>', f'<script src="data.js?v={VER}"></script>')
        .replace("sc.src = 'erep.js';", f"sc.src = 'erep.js?v={VER}';")
        .replace("sc.src = 'inbox.js';", f"sc.src = 'inbox.js?v={VER}';")
)

data_js = ROOT / "dashboard" / "data.js"
data_js.write_text(
    "window.__PORTFOLIO__ = " + json.dumps(portfolio, default=str) + ";\n"
    "window.__INSIGHT__ = " + json.dumps(insight, default=str) + ";\n"
)
erep = json.loads((ROOT / "dashboard" / "erep.json").read_text())
erep_js = ROOT / "dashboard" / "erep.js"
erep_js.write_text("window.__EREP__ = " + json.dumps(erep, default=str) + ";\n")
inbox = json.loads((ROOT / "dashboard" / "inbox.json").read_text())
inbox_js = ROOT / "dashboard" / "inbox.js"
inbox_js.write_text("window.__INBOX__ = " + json.dumps(inbox, default=str) + ";\n")
print(f"-> {out} ({out.stat().st_size//1024} KB) + data.js ({data_js.stat().st_size//1024} KB)"
      f" + erep.js ({erep_js.stat().st_size//1024} KB) + inbox.js ({inbox_js.stat().st_size//1024} KB)")
