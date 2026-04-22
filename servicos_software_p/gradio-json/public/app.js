const API_BASE = "/api";

const materiasList = document.getElementById("materias-list");
const compromissosList = document.getElementById("compromissos-list");
const tplMateria = document.getElementById("tpl-materia");
const tplCompromisso = document.getElementById("tpl-compromisso");
const form = document.getElementById("plano-form");
const statusText = document.getElementById("status-text");
const resultSection = document.getElementById("result-section");
const resultSummary = document.getElementById("result-summary");
const resultDias = document.getElementById("result-dias");
const resultObs = document.getElementById("result-obs");
const editHint = document.getElementById("edit-hint");
const resultToolbar = document.getElementById("result-toolbar");
const listaMaterias = document.getElementById("lista-materias");

let planoOriginal = null;

function pad2(n) {
  return String(n).padStart(2, "0");
}

function timeInputToHHMM(value) {
  if (!value) return "";
  const [h, m] = value.split(":");
  return `${pad2(Number(h))}:${pad2(Number(m))}`;
}

function hhmmToTimeInput(hhmm) {
  if (!hhmm || hhmm.length < 4) return "";
  const [h, m] = hhmm.split(":");
  return `${pad2(Number(h))}:${pad2(Number(m))}`;
}

function minutesFromHHMM(s) {
  const [h, m] = s.split(":").map(Number);
  return h * 60 + m;
}

function refreshDatalistMaterias() {
  listaMaterias.innerHTML = "";
  for (const row of materiasList.querySelectorAll(".materia-row")) {
    const nome = row.querySelector(".m-nome").value.trim();
    if (!nome) continue;
    const opt = document.createElement("option");
    opt.value = nome;
    listaMaterias.appendChild(opt);
  }
}

function addMateriaRow(preset) {
  const node = tplMateria.content.firstElementChild.cloneNode(true);
  if (preset?.nome) node.querySelector(".m-nome").value = preset.nome;
  if (preset?.dificuldade) node.querySelector(".m-dificuldade").value = preset.dificuldade;
  node.querySelector(".rm-materia").addEventListener("click", () => {
    node.remove();
    if (!materiasList.children.length) addMateriaRow({ nome: "", dificuldade: "media" });
  });
  materiasList.appendChild(node);
}

function addCompromissoRow(preset) {
  const node = tplCompromisso.content.firstElementChild.cloneNode(true);
  if (preset?.dia) node.querySelector(".c-dia").value = String(preset.dia);
  if (preset?.inicio) node.querySelector(".c-inicio").value = preset.inicio;
  if (preset?.fim) node.querySelector(".c-fim").value = preset.fim;
  node.querySelector(".rm-compromisso").addEventListener("click", () => node.remove());
  compromissosList.appendChild(node);
}

document.getElementById("add-materia").addEventListener("click", () => addMateriaRow());
document.getElementById("add-compromisso").addEventListener("click", () => addCompromissoRow({}));

function collectPayload() {
  const fd = new FormData(form);
  const materias = [...materiasList.querySelectorAll(".materia-row")].map((row) => ({
    nome: row.querySelector(".m-nome").value.trim(),
    dificuldade: row.querySelector(".m-dificuldade").value,
  }));

  const compromissos = [...compromissosList.querySelectorAll(".compromisso-row")]
    .map((row) => ({
      dia: Number(row.querySelector(".c-dia").value),
      inicio: timeInputToHHMM(row.querySelector(".c-inicio").value),
      fim: timeInputToHHMM(row.querySelector(".c-fim").value),
    }))
    .filter((c) => c.inicio && c.fim);

  return {
    dias_estudo: Number(fd.get("dias_estudo")),
    horas_por_dia: Number(fd.get("horas_por_dia")),
    objetivo: fd.get("objetivo"),
    pausas: "tipo_aula",
    periodo_preferido: fd.get("periodo_preferido"),
    compromissos,
    materias,
  };
}

function validateClient(payload) {
  if (!payload.materias.length) return "Adicione pelo menos uma matéria.";
  for (const m of payload.materias) {
    if (!m.nome) return "Cada matéria precisa de um nome.";
  }
  for (const c of payload.compromissos) {
    if (!Number.isFinite(c.dia) || c.dia < 1) {
      return "Compromissos precisam de um dia válido (inteiro ≥ 1) e horários completos.";
    }
    if (!c.inicio || !c.fim) return "Preencha início e fim de cada compromisso.";
    if (c.inicio >= c.fim) return "Em compromissos, o fim deve ser depois do início.";
    if (c.dia > payload.dias_estudo) {
      return `Compromisso no dia ${c.dia} excede os ${payload.dias_estudo} dias de estudo informados.`;
    }
  }
  if (!Number.isFinite(payload.horas_por_dia) || payload.horas_por_dia <= 0) {
    return "Informe horas por dia maior que zero.";
  }
  return null;
}

function setStatus(msg, kind) {
  statusText.textContent = msg || "";
  statusText.classList.remove("status--ok", "status--err");
  if (kind === "ok") statusText.classList.add("status--ok");
  if (kind === "err") statusText.classList.add("status--err");
}

function tipoClass(tipo) {
  if (tipo === "teoria") return "bloco--teoria";
  if (tipo === "exercicios") return "bloco--exercicios";
  return "bloco--pausa";
}

const BLOCO_EDIT_BASE_CLASS = "bloco bloco-edit";

function setBlocoEditVariantClasses(li) {
  const tipo = li.querySelector(".be-tipo").value;
  li.className = `${BLOCO_EDIT_BASE_CLASS} ${tipoClass(tipo)} ${
    tipo === "pausa" ? "bloco-edit--pausa" : "bloco-edit--aula"
  }`;
}

function syncMatDisabled(li) {
  const tipo = li.querySelector(".be-tipo").value;
  const inp = li.querySelector(".be-mat");
  inp.disabled = tipo === "pausa";
  if (tipo === "pausa") inp.value = "";
}

function tipoLegivel(tipo) {
  if (tipo === "exercicios") return "exercícios";
  if (tipo === "teoria") return "teoria";
  return "pausa";
}

function syncBlocoHeadline(li) {
  const horEl = li.querySelector(".bloco-headline__horario");
  const midEl = li.querySelector(".bloco-headline__mid");
  if (!horEl || !midEl) return;

  const ini = timeInputToHHMM(li.querySelector(".be-ini").value);
  const fim = timeInputToHHMM(li.querySelector(".be-fim").value);
  const tipo = li.querySelector(".be-tipo").value;
  const mat = (li.querySelector(".be-mat").value || "").trim();

  horEl.textContent = ini && fim ? `${ini}–${fim}` : "—";

  if (tipo === "pausa") {
    midEl.textContent = "Pausa";
  } else {
    const nome = mat || "Matéria";
    midEl.textContent = `${nome} (${tipoLegivel(tipo)})`;
  }

  setBlocoEditVariantClasses(li);
}

function duracaoBlocoRow(li) {
  const ini = timeInputToHHMM(li.querySelector(".be-ini").value);
  const fim = timeInputToHHMM(li.querySelector(".be-fim").value);
  if (!ini || !fim) return 0;
  return Math.max(0, minutesFromHHMM(fim) - minutesFromHHMM(ini));
}

function computeTotalsFromDOM() {
  let total = 0;
  for (const li of resultDias.querySelectorAll(".bloco-edit")) {
    total += duracaoBlocoRow(li);
  }
  const pill = resultSummary.querySelector(".pill--total");
  if (pill) pill.textContent = `Tempo total (blocos): ${total} min`;
}

function renderPlano(data, opts = {}) {
  const replaceOriginal = opts.replaceOriginal !== false;
  if (replaceOriginal) {
    planoOriginal = JSON.parse(JSON.stringify(data));
  }

  resultSection.hidden = false;
  editHint.hidden = false;
  resultToolbar.hidden = false;

  resultSummary.innerHTML = "";
  const p1 = document.createElement("span");
  p1.className = "pill pill--total";
  p1.textContent = `Tempo total (blocos): ${data.tempo_total_minutos} min`;
  resultSummary.appendChild(p1);

  refreshDatalistMaterias();
  resultDias.innerHTML = "";

  for (const dia of data.dias) {
    const card = document.createElement("article");
    card.className = "dia-card";
    card.dataset.diaNum = String(dia.dia);
    const h = document.createElement("h3");
    h.textContent = `Dia ${dia.dia}`;
    const ul = document.createElement("ul");
    ul.className = "blocos";

    for (const b of dia.blocos) {
      const li = document.createElement("li");
      li.className = BLOCO_EDIT_BASE_CLASS;
      li.innerHTML = `
        <div class="bloco-headline" aria-live="polite">
          <span class="bloco-headline__horario"></span>
          <span class="bloco-headline__sep"> - </span>
          <span class="bloco-headline__mid"></span>
        </div>
        <div class="bloco-edit__row">
          <div class="bloco-edit__times">
            <label class="be-label">Início<input type="time" class="be-ini" step="60" /></label>
            <span class="be-sep">–</span>
            <label class="be-label">Fim<input type="time" class="be-fim" step="60" /></label>
          </div>
          <label class="be-label">Tipo
            <select class="be-tipo">
              <option value="teoria">Teoria</option>
              <option value="exercicios">Exercícios</option>
              <option value="pausa">Pausa</option>
            </select>
          </label>
          <label class="be-label be-label--mat">Matéria
            <input type="text" class="be-mat" list="lista-materias" placeholder="—" autocomplete="off" />
          </label>
          <button type="button" class="btn btn--danger btn--icon rm-bloco" title="Remover bloco">✕</button>
        </div>
      `;
      li.querySelector(".be-ini").value = hhmmToTimeInput(b.inicio);
      li.querySelector(".be-fim").value = hhmmToTimeInput(b.fim);
      li.querySelector(".be-tipo").value = b.tipo;
      li.querySelector(".be-mat").value = b.materia || "";
      syncMatDisabled(li);
      syncBlocoHeadline(li);
      ul.appendChild(li);
    }

    if (!dia.blocos.length) {
      const empty = document.createElement("p");
      empty.className = "hint";
      empty.textContent = "Nenhum bloco neste dia (verifique compromissos ou janela).";
      card.appendChild(h);
      card.appendChild(empty);
    } else {
      card.appendChild(h);
      card.appendChild(ul);
    }
    resultDias.appendChild(card);
  }

  resultObs.innerHTML = "";
  resultObs.className = "observacoes observacoes--stack";

  const dicas = data.dicas_exercicios;
  if (dicas?.length) {
    const titulo = document.createElement("strong");
    titulo.className = "observacoes__titulo-principal";
    titulo.textContent = "Dicas e links para exercícios";
    resultObs.appendChild(titulo);

    const intro = document.createElement("p");
    intro.className = "observacoes__intro";
    intro.textContent =
      "Sugestões de busca por matéria. Os links abrem em nova aba; escolha fontes confiáveis.";
    resultObs.appendChild(intro);

    for (const dm of dicas) {
      const h = document.createElement("h4");
      h.className = "observacoes__materia";
      h.textContent = dm.materia;

      const ul = document.createElement("ul");
      ul.className = "observacoes__links";
      for (const item of dm.links) {
        const li = document.createElement("li");
        const a = document.createElement("a");
        a.href = item.url;
        a.textContent = item.titulo;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        li.appendChild(a);
        ul.appendChild(li);
      }
      resultObs.appendChild(h);
      resultObs.appendChild(ul);
    }
  }

  if (data.observacoes?.length) {
    const box = document.createElement("div");
    box.className = "observacoes__tecnicas";
    const st = document.createElement("strong");
    st.className = "observacoes__subtitulo";
    st.textContent = "Avisos do cronograma";
    const ul2 = document.createElement("ul");
    for (const o of data.observacoes) {
      const li = document.createElement("li");
      li.textContent = o;
      ul2.appendChild(li);
    }
    box.appendChild(st);
    box.appendChild(ul2);
    resultObs.appendChild(box);
  }

  computeTotalsFromDOM();
}

resultDias.addEventListener("input", (e) => {
  const li = e.target.closest(".bloco-edit");
  if (li && e.target.classList.contains("be-tipo")) syncMatDisabled(li);
  if (li) syncBlocoHeadline(li);
  computeTotalsFromDOM();
});

resultDias.addEventListener("change", (e) => {
  const li = e.target.closest(".bloco-edit");
  if (li && e.target.classList.contains("be-tipo")) syncMatDisabled(li);
  if (li) syncBlocoHeadline(li);
  computeTotalsFromDOM();
});

resultDias.addEventListener("click", (e) => {
  const btn = e.target.closest(".rm-bloco");
  if (!btn) return;
  const li = btn.closest(".bloco-edit");
  if (li) li.remove();
  computeTotalsFromDOM();
});

document.getElementById("btn-reset-plano").addEventListener("click", () => {
  if (!planoOriginal) return;
  renderPlano(planoOriginal, { replaceOriginal: false });
  setStatus("Plano restaurado ao retorno da API.", "ok");
});

document.getElementById("btn-atualizar-totais").addEventListener("click", () => {
  computeTotalsFromDOM();
  setStatus("Totais recalculados a partir dos horários atuais.", "ok");
});

async function pingHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error("health falhou");
    const data = await res.json();
    setStatus(`API disponível (${data.status}).`, "ok");
  } catch {
    setStatus("Não foi possível contatar /api/health — verifique o compose.", "err");
  }
}

form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const payload = collectPayload();
  const err = validateClient(payload);
  if (err) {
    setStatus(err, "err");
    return;
  }

  const btn = document.getElementById("submit-btn");
  btn.disabled = true;
  setStatus("Gerando plano…", null);

  try {
    const res = await fetch(`${API_BASE}/gerar-plano`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      let msg = `Erro ${res.status}`;
      try {
        const body = await res.json();
        if (body.erro) msg = body.erro;
        if (body.detalhes) msg += `: ${body.detalhes.join(" | ")}`;
      } catch {
      }
      throw new Error(msg);
    }

    const data = await res.json();
    renderPlano(data);
    setStatus("Plano gerado com sucesso. Você pode editar os blocos abaixo.", "ok");
  } catch (e) {
    setStatus(e.message || "Falha ao gerar plano.", "err");
  } finally {
    btn.disabled = false;
  }
});

addMateriaRow({ nome: "Matemática", dificuldade: "alta" });
addMateriaRow({ nome: "História", dificuldade: "media" });
pingHealth();
