const NAMED_COLORS = {
  white: [255, 255, 255, 1],
  black: [0, 0, 0, 1],
  transparent: [0, 0, 0, 0],
};

export function parseCssColor(value) {
  const color = String(value || '').trim().toLowerCase();
  if (!color) return null;
  if (NAMED_COLORS[color]) {
    const [r, g, b, a] = NAMED_COLORS[color];
    return { r, g, b, a };
  }

  const hex = color.match(/^#([0-9a-f]{3,8})$/i);
  if (hex) {
    let digits = hex[1];
    if (digits.length === 3 || digits.length === 4) {
      digits = [...digits].map(char => char + char).join('');
    }
    if (digits.length === 6 || digits.length === 8) {
      return {
        r: Number.parseInt(digits.slice(0, 2), 16),
        g: Number.parseInt(digits.slice(2, 4), 16),
        b: Number.parseInt(digits.slice(4, 6), 16),
        a: digits.length === 8 ? Number.parseInt(digits.slice(6, 8), 16) / 255 : 1,
      };
    }
  }

  const rgb = color.match(/^rgba?\(\s*([\d.]+)\s*[, ]\s*([\d.]+)\s*[, ]\s*([\d.]+)(?:\s*[,/]\s*([\d.]+%?))?\s*\)$/i);
  if (!rgb) return null;
  let alpha = 1;
  if (rgb[4]) {
    alpha = rgb[4].endsWith('%')
      ? Number.parseFloat(rgb[4]) / 100
      : Number.parseFloat(rgb[4]);
  }
  return {
    r: Math.max(0, Math.min(255, Number.parseFloat(rgb[1]))),
    g: Math.max(0, Math.min(255, Number.parseFloat(rgb[2]))),
    b: Math.max(0, Math.min(255, Number.parseFloat(rgb[3]))),
    a: Math.max(0, Math.min(1, alpha)),
  };
}

function compositeOver(color, background = [255, 255, 255]) {
  if (!color) return null;
  return [
    color.r * color.a + background[0] * (1 - color.a),
    color.g * color.a + background[1] * (1 - color.a),
    color.b * color.a + background[2] * (1 - color.a),
  ];
}

export function relativeLuminance(color) {
  const parsed = typeof color === 'string' ? parseCssColor(color) : color;
  if (!parsed) return 1;
  const channels = compositeOver(parsed).map(value => {
    const channel = value / 255;
    return channel <= 0.04045
      ? channel / 12.92
      : ((channel + 0.055) / 1.055) ** 2.4;
  });
  return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
}

export function contrastRatio(background, foreground) {
  const first = relativeLuminance(background);
  const second = relativeLuminance(foreground);
  return (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05);
}

export function classifyContentSurface(value) {
  const parsed = parseCssColor(value);
  if (!parsed || parsed.a < 0.12) return null;
  const luminance = relativeLuminance(parsed);
  if (luminance <= 0.32) return 'dark';
  if (luminance >= 0.72) return 'light';
  return null;
}

function toHex(color) {
  return `#${[color.r, color.g, color.b]
    .map(value => Math.round(value).toString(16).padStart(2, '0'))
    .join('')}`;
}

export function chooseReadableColor(background, preferred) {
  const parsedBackground = parseCssColor(background) || parseCssColor('#ffffff');
  const parsedPreferred = parseCssColor(preferred);
  if (parsedPreferred && contrastRatio(parsedBackground, parsedPreferred) >= 4.5) {
    return toHex(parsedPreferred);
  }
  return relativeLuminance(parsedBackground) < 0.5 ? '#e8eef8' : '#334155';
}

export function adaptiveColorPair(preferred) {
  return {
    light: chooseReadableColor('#ffffff', preferred),
    dark: chooseReadableColor('#111827', preferred),
  };
}

export function extractStyleColor(style, property = 'color') {
  const escaped = property.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = String(style || '').match(new RegExp(`(?:^|;)\\s*${escaped}\\s*:\\s*([^;]+)`, 'i'));
  return match?.[1]?.trim() || '';
}

export function extractBackgroundColor(style) {
  const explicit = extractStyleColor(style, 'background-color');
  if (explicit) return explicit;
  const shorthand = extractStyleColor(style, 'background');
  const token = shorthand.match(
    /#[0-9a-f]{3,8}\b|rgba?\([^)]*\)|\b(?:white|black|transparent)\b/i,
  );
  return token?.[0] || '';
}

export function normalizeContentContrast(root) {
  if (!root?.querySelectorAll) return root;
  root.classList?.add('content-contrast-normalized');
  const elements = [root, ...root.querySelectorAll('*')];
  for (const element of elements) {
    const style = element.getAttribute?.('style') || '';
    const ownBackground = extractBackgroundColor(style);
    const ownSurface = element.tagName?.toLowerCase() === 'pre'
      ? 'dark'
      : classifyContentSurface(ownBackground);
    if (ownSurface) element.setAttribute('data-content-surface', ownSurface);
    const inheritedSurface = ownSurface
      || element.parentElement?.closest?.('[data-content-surface]')?.getAttribute('data-content-surface')
      || '';
    const explicitColor = extractStyleColor(style, 'color');
    if (!explicitColor) continue;

    if (inheritedSurface) {
      const background = inheritedSurface === 'dark' ? '#111827' : '#ffffff';
      const readable = chooseReadableColor(background, explicitColor);
      if (contrastRatio(background, explicitColor) < 4.5) {
        element.style.setProperty('color', readable, 'important');
      }
      continue;
    }

    const pair = adaptiveColorPair(explicitColor);
    if (pair.light !== pair.dark) {
      element.style.removeProperty('color');
      element.style.setProperty('--content-light-color', pair.light);
      element.style.setProperty('--content-dark-color', pair.dark);
      element.classList.add('content-adaptive-color');
    }
  }
  return root;
}

export function normalizeHtmlContrast(html) {
  if (!html || typeof DOMParser === 'undefined') return html || '';
  const documentNode = new DOMParser().parseFromString(
    `<div id="contrast-root">${html}</div>`,
    'text/html',
  );
  const root = documentNode.querySelector('#contrast-root');
  normalizeContentContrast(root);
  return root?.innerHTML || html;
}
