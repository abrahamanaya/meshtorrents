// Widget de inserción automática de enlaces de afiliados para MeshTorrents.
// Se importa como módulo ES desde index.html: import { ... } from './affiliates.js';

const API_BASE = window.MESHTORRENTS_API_BASE || 'http://localhost:8000/api';

// Traduce la categoría de un modelo 3D a la categoría de insumo más relevante.
const MODEL_TO_AFFILIATE_CATEGORY = {
  'Miniaturas': 'resinas',
  'Herramientas': 'filamentos',
  'Repuestos': 'filamentos',
  'Decoración': 'filamentos',
  'Otros': 'general',
};

export function mapModelCategory(modelCategory) {
  return MODEL_TO_AFFILIATE_CATEGORY[modelCategory] || 'general';
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

export function clickUrl(link) {
  return `${API_BASE}/affiliates/${link.id}/click`;
}

export async function fetchRandomAffiliates(category, count = 1) {
  const params = new URLSearchParams();
  if (category) params.set('category', category);
  params.set('count', String(count));

  try {
    const res = await fetch(`${API_BASE}/affiliates/random?${params.toString()}`);
    if (!res.ok) return [];
    return await res.json();
  } catch (err) {
    return [];
  }
}

const affiliateLinkAttrs = 'target="_blank" rel="noopener noreferrer sponsored"';

// --- 1. Banner compacto: debajo del visor 3D ---
function renderCompactBanner(link) {
  return `
    <a href="${clickUrl(link)}" ${affiliateLinkAttrs}
      class="flex items-center gap-3 bg-surface2 border border-border rounded-lg px-3 py-2 hover:border-accent/40 transition group">
      ${link.image_url
        ? `<img src="${escapeHtml(link.image_url)}" alt="" class="h-10 w-10 rounded object-cover shrink-0" loading="lazy" />`
        : `<div class="h-10 w-10 rounded bg-surface flex items-center justify-center text-slate-600 shrink-0">◆</div>`}
      <div class="min-w-0 flex-1">
        <p class="text-[10px] uppercase tracking-wide text-accent/80">Recomendado para este modelo</p>
        <p class="text-sm text-slate-200 truncate group-hover:text-white">${escapeHtml(link.title)}</p>
      </div>
      ${link.price_hint ? `<span class="text-xs font-medium text-accent shrink-0">${escapeHtml(link.price_hint)}</span>` : ''}
      <span class="text-slate-500 group-hover:text-accent shrink-0">→</span>
    </a>
  `;
}

// --- 2. Tarjeta de insumo: bloque "Insumos recomendados para este modelo" ---
function renderSupplyCard(link) {
  return `
    <a href="${clickUrl(link)}" ${affiliateLinkAttrs}
      class="block bg-surface2 border border-border rounded-lg overflow-hidden hover:border-accent/40 transition group">
      <div class="h-24 bg-surface overflow-hidden">
        ${link.image_url
          ? `<img src="${escapeHtml(link.image_url)}" alt="" class="w-full h-full object-cover group-hover:scale-105 transition" loading="lazy" />`
          : `<div class="w-full h-full flex items-center justify-center text-slate-600 text-2xl">◆</div>`}
      </div>
      <div class="p-2.5">
        <p class="text-xs text-slate-200 leading-snug line-clamp-2">${escapeHtml(link.title)}</p>
        <div class="flex items-center justify-between mt-1.5">
          ${link.price_hint ? `<span class="text-xs font-medium text-accent">${escapeHtml(link.price_hint)}</span>` : '<span></span>'}
          <span class="text-[10px] text-slate-500 group-hover:text-accent">Ver oferta →</span>
        </div>
      </div>
    </a>
  `;
}

// --- 3. Banner rotativo de sidebar: "Ofertas Maker del Día" ---
function renderSidebarBanner(link) {
  return `
    <a href="${clickUrl(link)}" ${affiliateLinkAttrs}
      class="block bg-gradient-to-br from-surface2 to-surface border border-accent/20 rounded-xl overflow-hidden hover:border-accent/50 transition group glow">
      <div class="h-32 bg-surface overflow-hidden">
        ${link.image_url
          ? `<img src="${escapeHtml(link.image_url)}" alt="" class="w-full h-full object-cover group-hover:scale-105 transition" loading="lazy" />`
          : `<div class="w-full h-full flex items-center justify-center text-slate-600 text-3xl">◆</div>`}
      </div>
      <div class="p-3">
        <p class="text-[10px] uppercase tracking-wide text-accent2">Oferta Maker del día</p>
        <p class="text-sm text-slate-100 leading-snug mt-1">${escapeHtml(link.title)}</p>
        <div class="flex items-center justify-between mt-2">
          ${link.price_hint ? `<span class="text-sm font-semibold text-accent">${escapeHtml(link.price_hint)}</span>` : '<span></span>'}
          <span class="text-xs text-slate-400 group-hover:text-accent">Ver en ML →</span>
        </div>
      </div>
    </a>
  `;
}

/** Monta el banner compacto de recomendación justo debajo del visor 3D. */
export async function mountViewerRecommendation(container, modelCategory) {
  if (!container) return;
  container.innerHTML = '<p class="text-xs text-slate-600">Cargando recomendación…</p>';
  const [link] = await fetchRandomAffiliates(mapModelCategory(modelCategory), 1);
  container.innerHTML = link ? renderCompactBanner(link) : '';
}

/** Monta el bloque "Insumos recomendados para este modelo" (grid de N tarjetas). */
export async function mountRecommendedSupplies(container, modelCategory, count = 3) {
  if (!container) return;
  container.innerHTML = '<p class="text-xs text-slate-600">Cargando insumos recomendados…</p>';
  const links = await fetchRandomAffiliates(mapModelCategory(modelCategory), count);

  if (!links.length) {
    container.innerHTML = '';
    return;
  }

  container.innerHTML = `
    <h4 class="text-sm font-medium text-white mb-2">Insumos recomendados para este modelo</h4>
    <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">${links.map(renderSupplyCard).join('')}</div>
    <p class="text-[10px] text-slate-600 mt-2">Enlaces de afiliado — MeshTorrents puede recibir una comisión sin costo extra para ti.</p>
  `;
}

/** Monta y rota automáticamente el banner "Ofertas Maker del Día" en el sidebar. */
export function mountSidebarRotatingBanner(container, { intervalMs = 15000 } = {}) {
  if (!container) return () => {};

  let timer = null;
  let cancelled = false;

  async function rotate() {
    const [link] = await fetchRandomAffiliates(null, 1);
    if (cancelled) return;

    container.style.opacity = '0';
    setTimeout(() => {
      if (cancelled) return;
      container.innerHTML = link
        ? renderSidebarBanner(link)
        : '<p class="text-xs text-slate-600">Sin ofertas disponibles por ahora.</p>';
      container.style.opacity = '1';
    }, 200);
  }

  rotate();
  timer = setInterval(rotate, intervalMs);

  // Devuelve una función de limpieza para detener la rotación si el widget se desmonta.
  return () => {
    cancelled = true;
    clearInterval(timer);
  };
}
