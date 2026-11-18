(() => {
  const $ = (selector) => document.querySelector(selector);
  const fmt = (value, digits = 0) => value == null || Number.isNaN(Number(value)) ? '—' : Number(value).toLocaleString('en-IN', { maximumFractionDigits: digits, minimumFractionDigits: digits });
  const pct = (value) => `${fmt(value, 1)}%`;
  const score = (value) => fmt(value, 1);
  const state = { data: null, type: 'batters' };



  function fillCoverage(data) {
    const s = data.scope;
    $('#matches-count').textContent = fmt(s.match_count);
    $('#deliveries-count').textContent = fmt(s.delivery_count);
    $('#pressure-count').textContent = fmt(s.pressure_delivery_count);
    $('#pressure-matches').textContent = fmt(s.pressure_match_count);
    $('#pressure-share').textContent = `${pct(100*s.pressure_delivery_count/s.delivery_count)} of analysed balls`;
    $('#ipl-matches').textContent = fmt(s.ipl_match_count);
    $('#t20i-matches').textContent = fmt(s.t20i_match_count);
    $('#eligible-count').textContent = `${fmt(s.eligible_batter_count)} batters · ${fmt(s.eligible_bowler_count)} bowlers`;
    const reasons = s.pressure_reason_counts || {};
    $('#pressure-late-count').textContent = `${fmt(reasons['First-innings late/wicket/run-rate stress'])} deliveries tagged`;
    $('#pressure-chase-count').textContent = `${fmt(reasons['Chase: RRR >= 9 in final 10 overs'])} deliveries tagged`;
    $('#pressure-collapse-count').textContent = `${fmt(reasons['Chase: high RRR with wickets down or in final 5 overs'])} deliveries tagged`;
  }

  function renderWeights(target, items) {
    $(target).innerHTML = items.map(([label, weight]) => `
      <div class="weight-row"><span>${escapeHtml(label)}</span><div class="weight-track"><i style="width:${weight*100}%"></i></div><b>${weight*100}%</b></div>
    `).join('');
  }

  const batterWeights = [
    ['Pressure strike rate', .30], ['Strike-rate uplift vs baseline', .25],
    ['Smoothed-average uplift', .15], ['Boundary-rate uplift', .15], ['Pressure-innings consistency', .15]
  ];
  const bowlerWeights = [
    ['Wickets / 24 pressure balls', .28], ['Pressure economy', .24],
    ['Economy improvement vs baseline', .18], ['Pressure dot-ball rate', .12],
    ['Dot-rate uplift vs baseline', .08], ['Pressure-outing consistency', .10]
  ];

  function renderBatters(rows) {
    const target = $('#batter-rows');
    if (!rows.length) { target.innerHTML = '<tr><td colspan="9" class="no-results">No batters match this search.</td></tr>'; return; }
    target.innerHTML = rows.map(p => `
      <tr data-kind="batter" data-id="${p.striker_id}" tabindex="0" aria-label="Open ${escapeHtml(p.striker_name)} details">
        <td><span class="rank-num">${String(p.rank).padStart(2,'0')}</span></td>
        <td><span class="player-name">${escapeHtml(p.striker_name)}</span></td>
        <td><div class="score-cell"><span class="score-number">${score(p.score)}</span><span class="score-track"><i style="width:${Math.max(0,Math.min(100,p.score))}%"></i></span></div></td>
        <td><b>${fmt(p.runs_p)}</b> <span class="muted-inline">/ ${fmt(p.balls_p)} balls</span></td>
        <td>${fmt(p.sr_p,1)}</td><td>${fmt(p.avg_p,1)}</td><td>${fmt(p.matches_p)}</td><td>${fmt(p.sr_n,1)}</td><td><span class="table-arrow">↗</span></td>
      </tr>`).join('');
  }

  function renderBowlers(rows) {
    const target = $('#bowler-rows');
    if (!rows.length) { target.innerHTML = '<tr><td colspan="9" class="no-results">No bowlers match this search.</td></tr>'; return; }
    target.innerHTML = rows.map(p => `
      <tr data-kind="bowler" data-id="${p.bowler_id}" tabindex="0" aria-label="Open ${escapeHtml(p.bowler_name)} details">
        <td><span class="rank-num">${String(p.rank).padStart(2,'0')}</span></td>
        <td><span class="player-name">${escapeHtml(p.bowler_name)}</span></td>
        <td><div class="score-cell"><span class="score-number">${score(p.score)}</span><span class="score-track"><i style="width:${Math.max(0,Math.min(100,p.score))}%"></i></span></div></td>
        <td><b>${fmt(p.wickets_p)}</b> <span class="muted-inline">/ ${fmt(p.balls_p)} balls</span></td>
        <td>${fmt(p.econ_p,2)}</td><td>${fmt(p.wickets_per24_p,2)}</td><td>${fmt(p.matches_p)}</td><td>${fmt(p.econ_n,2)}</td><td><span class="table-arrow">↗</span></td>
      </tr>`).join('');
  }

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, (ch) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  }

  function playerDetails(kind, p) {
    const isBat = kind === 'batter';
    const name = isBat ? p.striker_name : p.bowler_name;
    const role = isBat ? 'BATTER' : 'BOWLER';
    const metrics = isBat ? [
      ['Pressure runs', fmt(p.runs_p)], ['Pressure balls', fmt(p.balls_p)], ['Pressure strike rate', fmt(p.sr_p,1)],
      ['Smoothed pressure average', fmt(p.avg_p,1)], ['Boundary rate', pct(p.boundary_pct_p)], ['Pressure matches', fmt(p.matches_p)],
      ['Non-pressure SR', fmt(p.sr_n,1)], ['SR change', `${p.delta_sr >= 0 ? '+' : ''}${fmt(p.delta_sr,1)}`]
    ] : [
      ['Pressure wickets', fmt(p.wickets_p)], ['Pressure legal balls', fmt(p.balls_p)], ['Pressure economy', fmt(p.econ_p,2)],
      ['Wickets / 24 balls', fmt(p.wickets_per24_p,2)], ['Dot-ball rate', pct(p.dot_pct_p)], ['Pressure matches', fmt(p.matches_p)],
      ['Non-pressure economy', fmt(p.econ_n,2)], ['Economy improvement', `${p.delta_economy >= 0 ? '+' : ''}${fmt(p.delta_economy,2)}`]
    ];
    const baseline = isBat ? [['Non-pressure runs',fmt(p.runs_n)],['Non-pressure balls',fmt(p.balls_n)],['Non-pressure average',fmt(p.avg_n,1)],['Non-pressure boundary rate',pct(p.boundary_pct_n)]] : [['Non-pressure wickets',fmt(p.wickets_n)],['Non-pressure legal balls',fmt(p.balls_n)],['Non-pressure wickets / 24',fmt(p.wickets_per24_n,2)],['Non-pressure dot rate',pct(p.dot_pct_n)]];
    const ex = p.evidence_match;
    const evidence = ex ? (isBat
      ? `<strong>${escapeHtml(ex.match_date)} · ${escapeHtml(ex.competition)}</strong><br>${escapeHtml(ex.opponent)} — ${fmt(ex.pressure_runs)} pressure runs from ${fmt(ex.pressure_balls)} pressure balls.<br><span>${escapeHtml(ex.match_result)}</span>`
      : `<strong>${escapeHtml(ex.match_date)} · ${escapeHtml(ex.competition)}</strong><br>${escapeHtml(ex.opponent)} — ${fmt(ex.pressure_wickets)} pressure wickets, ${fmt(ex.pressure_runs_conceded)} runs conceded from ${fmt(ex.pressure_legal_balls)} legal balls.<br><span>${escapeHtml(ex.match_result)}</span>`)
      : 'No single-match illustration available.';
    return `
      <div class="drawer-rank">RANK ${String(p.rank).padStart(2,'0')} / ${role}</div>
      <h2 class="drawer-title">${escapeHtml(name)}</h2>
      <div class="drawer-kicker">${escapeHtml(p.format_mix)} sample · Supplied data window 2022–2026</div>
      <div class="drawer-score"><div><small>PRESSURE MODEL SCORE</small><strong>${score(p.score)}</strong></div><span class="source-type">PERCENTILE-WEIGHTED</span></div>
      <div class="drawer-stat-grid">${metrics.map(([k,v])=>`<div class="drawer-stat"><small>${escapeHtml(k)}</small><b>${escapeHtml(v)}</b></div>`).join('')}</div>
      <div class="drawer-section-title">BASELINE / NON-PRESSURE PLAY</div>
      <div class="drawer-compare">${baseline.map(([k,v])=>`<div class="drawer-compare-row"><span>${escapeHtml(k)}</span><b>${escapeHtml(v)}</b></div>`).join('')}</div>
      <div class="drawer-section-title">ONE MATCH EXAMPLE · NOT THE BASIS OF THE RANK</div>
      <div class="drawer-evidence">${evidence}</div>
      <div class="drawer-section-title">INTERPRETATION</div>
      <div class="drawer-evidence">This is a retrospective performance ranking in the supplied IPL/T20I sample. It does not establish current playing status, fitness or future performance.</div>
    `;
  }

  function openDrawer(kind, id) {
    const rows = kind === 'batter' ? state.data.rankings.batters : state.data.rankings.bowlers;
    const p = rows.find(x => String(kind === 'batter' ? x.striker_id : x.bowler_id) === String(id));
    if (!p) return;
    $('#drawer-content').innerHTML = playerDetails(kind, p);
    $('#detail-drawer').classList.add('open');
    $('#detail-backdrop').classList.add('open');
    $('#detail-drawer').setAttribute('aria-hidden','false');
  }
  function closeDrawer() {
    $('#detail-drawer').classList.remove('open');
    $('#detail-backdrop').classList.remove('open');
    $('#detail-drawer').setAttribute('aria-hidden','true');
  }

  function attachRowEvents() {
    document.addEventListener('click', (e) => {
      const row = e.target.closest('tr[data-kind]');
      if (row) openDrawer(row.dataset.kind, row.dataset.id);
    });
    document.addEventListener('keydown', (e) => {
      const row = e.target.closest && e.target.closest('tr[data-kind]');
      if (row && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); openDrawer(row.dataset.kind,row.dataset.id); }
    });
    $('#drawer-close').addEventListener('click', closeDrawer);
    $('#detail-backdrop').addEventListener('click', closeDrawer);
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeDrawer(); });
  }

  function setupCompare() {
    const kind = $('#compare-kind');
    const a = $('#compare-a'); const b = $('#compare-b');
    const refreshOptions = () => {
      const arr = kind.value === 'batter' ? state.data.rankings.batters : state.data.rankings.bowlers;
      const idKey = kind.value === 'batter' ? 'striker_id' : 'bowler_id';
      const nameKey = kind.value === 'batter' ? 'striker_name' : 'bowler_name';
      const opts = arr.map(p => `<option value="${p[idKey]}">${escapeHtml(p.rank + '. ' + p[nameKey])}</option>`).join('');
      a.innerHTML=opts; b.innerHTML=opts; if(arr.length>1)b.selectedIndex=1;
      renderCompare();
    };
    const renderCompare = () => {
      const arr = kind.value === 'batter' ? state.data.rankings.batters : state.data.rankings.bowlers;
      const idKey = kind.value === 'batter' ? 'striker_id' : 'bowler_id';
      const p1=arr.find(p=>String(p[idKey])===a.value); const p2=arr.find(p=>String(p[idKey])===b.value);
      if(!p1||!p2){$('#compare-result').innerHTML='';return;}
      const isBat=kind.value==='batter';
      const nameKey=isBat?'striker_name':'bowler_name';
      const ms=isBat?[['Pressure strike rate','sr_p','sr_n',0],['Smoothed pressure average','avg_p','avg_n',0],['Boundary rate','boundary_pct_p','boundary_pct_n',0],['Pressure sample (matches)','matches_p',null,0]]:[['Pressure economy','econ_p','econ_n',2],['Wickets / 24 balls','wickets_per24_p','wickets_per24_n',2],['Dot-ball rate','dot_pct_p','dot_pct_n',1],['Pressure sample (matches)','matches_p',null,0]];
      const card=(p)=>`<article class="compare-card"><h3>${escapeHtml(p[nameKey])}</h3><div class="compare-sub">Rank ${p.rank} · score ${score(p.score)}</div>${ms.map(([label,key,base,dp])=>{const v=Number(p[key]||0);const max= Math.max(1, ...arr.map(r=>Number(r[key]||0)));const width=Math.max(2,Math.min(100,100*v/max));const baseTxt=base?` <span class="muted-inline">(baseline ${fmt(p[base],dp)})</span>`:'';return `<div class="compare-metric"><span>${label}${baseTxt}</span><div class="compare-bar"><i style="width:${width}%"></i></div><b class="compare-val">${fmt(v,dp)}</b></div>`}).join('')}</article>`;
      $('#compare-result').innerHTML=card(p1)+card(p2);
    };
    kind.addEventListener('change',refreshOptions);a.addEventListener('change',renderCompare);b.addEventListener('change',renderCompare);refreshOptions();
  }

  function setupScenarioFinder() {
    const select = $('#scenario-select');
    const run = $('#scenario-run');
    const output = $('#scenario-results');
    const explanation = $('#scenario-explanation');
    if (!select || !run || !output || !explanation) return;

    const scenarios = {
      chase: {
        title: 'Difficult chase: prioritise scoring speed without ignoring survival.',
        kind: 'batter',
        score: p => 0.38 * percentile(state.data.rankings.batters, 'sr_p', p.sr_p, true)
          + 0.24 * percentile(state.data.rankings.batters, 'avg_p', p.avg_p, true)
          + 0.23 * percentile(state.data.rankings.batters, 'delta_sr', p.delta_sr, true)
          + 0.15 * percentile(state.data.rankings.batters, 'matches_p', p.matches_p, true),
        reason: p => `Pressure SR ${fmt(p.sr_p,1)}; pressure average ${fmt(p.avg_p,1)}; ${fmt(p.matches_p)} pressure matches.`
      },
      rescue: {
        title: 'Wicket recovery: favour players with a higher smoothed pressure average and a meaningful match sample.',
        kind: 'batter',
        score: p => 0.42 * percentile(state.data.rankings.batters, 'avg_p', p.avg_p, true)
          + 0.28 * percentile(state.data.rankings.batters, 'matches_p', p.matches_p, true)
          + 0.18 * percentile(state.data.rankings.batters, 'runs_p', p.runs_p, true)
          + 0.12 * percentile(state.data.rankings.batters, 'sr_p', p.sr_p, true),
        reason: p => `Smoothed pressure average ${fmt(p.avg_p,1)} from ${fmt(p.matches_p)} pressure matches; ${fmt(p.runs_p)} pressure runs.`
      },
      finish: {
        title: 'Late acceleration: favour pressure strike rate and boundary frequency.',
        kind: 'batter',
        score: p => 0.42 * percentile(state.data.rankings.batters, 'sr_p', p.sr_p, true)
          + 0.32 * percentile(state.data.rankings.batters, 'boundary_pct_p', p.boundary_pct_p, true)
          + 0.16 * percentile(state.data.rankings.batters, 'matches_p', p.matches_p, true)
          + 0.10 * percentile(state.data.rankings.batters, 'delta_sr', p.delta_sr, true),
        reason: p => `Pressure SR ${fmt(p.sr_p,1)}; boundary rate ${pct(p.boundary_pct_p)}; ${fmt(p.matches_p)} pressure matches.`
      },
      defend: {
        title: 'Defend a total: favour lower pressure economy, dot balls and wickets.',
        kind: 'bowler',
        score: p => 0.38 * percentile(state.data.rankings.bowlers, 'econ_p', p.econ_p, false)
          + 0.26 * percentile(state.data.rankings.bowlers, 'dot_pct_p', p.dot_pct_p, true)
          + 0.24 * percentile(state.data.rankings.bowlers, 'wickets_per24_p', p.wickets_per24_p, true)
          + 0.12 * percentile(state.data.rankings.bowlers, 'matches_p', p.matches_p, true),
        reason: p => `Pressure economy ${fmt(p.econ_p,2)}; dot-ball rate ${pct(p.dot_pct_p)}; ${fmt(p.wickets_p)} pressure wickets.`
      },
      wickets: {
        title: 'Break a partnership: favour pressure wicket rate while checking economy and sample size.',
        kind: 'bowler',
        score: p => 0.43 * percentile(state.data.rankings.bowlers, 'wickets_per24_p', p.wickets_per24_p, true)
          + 0.24 * percentile(state.data.rankings.bowlers, 'wickets_p', p.wickets_p, true)
          + 0.18 * percentile(state.data.rankings.bowlers, 'matches_p', p.matches_p, true)
          + 0.15 * percentile(state.data.rankings.bowlers, 'econ_p', p.econ_p, false),
        reason: p => `${fmt(p.wickets_per24_p,2)} wickets per 24 pressure balls; ${fmt(p.wickets_p)} pressure wickets; pressure economy ${fmt(p.econ_p,2)}.`
      }
    };

    function percentile(rows, key, value, higherBetter) {
      const vals = rows.map(x => Number(x[key])).filter(Number.isFinite).sort((a,b)=>a-b);
      if (!vals.length) return 0;
      const below = vals.filter(v => v < Number(value)).length;
      const equal = vals.filter(v => v === Number(value)).length;
      const rank = (below + equal/2) / vals.length * 100;
      return higherBetter ? rank : 100-rank;
    }

    function render() {
      const cfg = scenarios[select.value];
      const rows = cfg.kind === 'batter' ? state.data.rankings.batters : state.data.rankings.bowlers;
      const nameKey = cfg.kind === 'batter' ? 'striker_name' : 'bowler_name';
      const ranked = rows.map(p => ({ player:p, scenarioScore:cfg.score(p) }))
        .sort((a,b)=>b.scenarioScore-a.scenarioScore).slice(0,3);
      explanation.textContent = cfg.title + ' This is a transparent re-weighting of the existing pressure metrics, not a separately trained prediction model.';
      output.innerHTML = ranked.map((item,i)=>{
        const p=item.player;
        return `<article class="scenario-result-card"><div class="scenario-result-rank">OPTION 0${i+1}</div><div class="scenario-result-main"><h3>${escapeHtml(p[nameKey])}</h3><span>Original pressure rank #${p.rank} · scenario fit ${fmt(item.scenarioScore,1)}/100</span><p>${cfg.reason(p)}</p></div></article>`;
      }).join('');
    }
    run.addEventListener('click',render);
    select.addEventListener('change',render);
    render();
  }

  function setNavSpy() {
    const links=[...document.querySelectorAll('.nav-link')];
    const sections=links.map(a=>document.querySelector(a.getAttribute('href'))).filter(Boolean);
    const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){links.forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+entry.target.id));}}),{rootMargin:'-25% 0px -65% 0px'});
    sections.forEach(s=>observer.observe(s));
  }

  async function init() {
    try {
      const response=await fetch('./data/dashboard.json');
      if(!response.ok)throw new Error('Could not load dashboard results');
      state.data=await response.json();
      fillCoverage(state.data);
      renderWeights('#batter-weights',batterWeights);
      renderWeights('#bowler-weights',bowlerWeights);
      renderBatters(state.data.rankings.batters);
      renderBowlers(state.data.rankings.bowlers);
      $('#batter-search').addEventListener('input',e=>renderBatters(state.data.rankings.batters.filter(p=>p.striker_name.toLowerCase().includes(e.target.value.toLowerCase()))));
      $('#bowler-search').addEventListener('input',e=>renderBowlers(state.data.rankings.bowlers.filter(p=>p.bowler_name.toLowerCase().includes(e.target.value.toLowerCase()))));
      attachRowEvents();setupCompare();setupScenarioFinder();setNavSpy();
    } catch (error) {
      document.querySelector('.main-content').insertAdjacentHTML('afterbegin',`<div style="padding:18px 28px;background:#fff0e8;color:#84482d">Dashboard data could not load: ${escapeHtml(error.message)}. Open this site through a local web server, not as a file:// URL.</div>`);
    }
  }
  document.addEventListener('DOMContentLoaded',init);
})();
