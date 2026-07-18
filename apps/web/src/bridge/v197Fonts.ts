import bodoniExactItalicUrl from "../assets/fonts/bodoni-moda-v28-latin-italic.woff2?url";
import bodoniExactNormalUrl from "../assets/fonts/bodoni-moda-v28-latin-normal.woff2?url";
import bodoni600NormalUrl from "@fontsource/bodoni-moda/files/bodoni-moda-latin-600-normal.woff2?url";
import crimsonExactItalicUrl from "../assets/fonts/crimson-pro-v28-latin-italic.woff2?url";
import crimsonExactNormalUrl from "../assets/fonts/crimson-pro-v28-latin-normal.woff2?url";
import crimson600ItalicUrl from "@fontsource/crimson-pro/files/crimson-pro-latin-600-italic.woff2?url";
import crimson600NormalUrl from "@fontsource/crimson-pro/files/crimson-pro-latin-600-normal.woff2?url";

type FontStyle = "normal" | "italic";

function fontFace(family: string, weight: number, style: FontStyle, source: string): string {
  return `@font-face {
    font-family: "${family}";
    font-style: ${style};
    font-display: swap;
    font-weight: ${weight};
    src: url("${source}") format("woff2");
  }`;
}

export const V197_FONT_FACE_CSS = [
  fontFace("Crimson Pro", 300, "normal", crimsonExactNormalUrl),
  fontFace("Crimson Pro", 300, "italic", crimsonExactItalicUrl),
  fontFace("Crimson Pro", 400, "normal", crimsonExactNormalUrl),
  fontFace("Crimson Pro", 400, "italic", crimsonExactItalicUrl),
  fontFace("Crimson Pro", 500, "normal", crimsonExactNormalUrl),
  fontFace("Crimson Pro", 500, "italic", crimsonExactItalicUrl),
  fontFace("Crimson Pro", 600, "normal", crimson600NormalUrl),
  fontFace("Crimson Pro", 600, "italic", crimson600ItalicUrl),
  fontFace("Bodoni Moda", 400, "normal", bodoniExactNormalUrl),
  fontFace("Bodoni Moda", 400, "italic", bodoniExactItalicUrl),
  fontFace("Bodoni Moda", 500, "normal", bodoniExactNormalUrl),
  fontFace("Bodoni Moda", 600, "normal", bodoni600NormalUrl),
].join("\n");
