'use client'

import katex from 'katex'
import 'katex/dist/katex.min.css'

interface Props {
  texto: string
  className?: string
}

// Divide o texto em partes: $$bloco$$, $inline$ e texto puro
// Lookbehind negativo: $ de LaTeX nunca vem depois de letra ou dígito (ex: R$150,00)
const REGEX_LATEX = /(\$\$[\s\S]+?\$\$|(?<![A-Za-z0-9])\$[^$\n]+?\$)/g

function renderParte(parte: string): string {
  // Bloco: $$...$$
  if (parte.startsWith('$$') && parte.endsWith('$$') && parte.length > 4) {
    try {
      return katex.renderToString(parte.slice(2, -2).trim(), {
        displayMode: true,
        throwOnError: false,
        trust: false,
      })
    } catch {
      return escapeHtml(parte)
    }
  }
  // Inline: $...$
  if (parte.startsWith('$') && parte.endsWith('$') && parte.length > 2) {
    try {
      return katex.renderToString(parte.slice(1, -1).trim(), {
        displayMode: false,
        throwOnError: false,
        trust: false,
      })
    } catch {
      return escapeHtml(parte)
    }
  }
  // Texto puro
  return escapeHtml(parte).replace(/\n/g, '<br />')
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

export default function TextoLatex({ texto, className }: Props) {
  if (!texto) return null

  const partes = texto.split(REGEX_LATEX)
  const html = partes.map(renderParte).join('')

  return (
    <span
      className={className}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
