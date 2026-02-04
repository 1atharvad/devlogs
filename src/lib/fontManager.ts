type FontWeights = string | number[];

export type FontConfig = {
  name: string;
  weights?: FontWeights;
};

const buildFontParam = (font: FontConfig) => {
  const family = font.name.replace(/ /g, '+');
  const weights = font.weights?.length
    ? `:wght@${typeof font.weights === 'string'
      ? font.weights
      : font.weights.join(';')}`
    : '';
  return `family=${family}${weights}`;
};

export const buildGoogleFontsUrl = (fonts: FontConfig[]) => {
  const base = 'https://fonts.googleapis.com/css2?';
  const params = fonts.map(buildFontParam).join('&');
  return `${base}${params}&display=swap`;
};
