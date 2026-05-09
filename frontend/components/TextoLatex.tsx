'use client'

import katex from 'katex'
import 'katex/dist/katex.min.css'

interface Props {
  texto: string
}

export default function TextoLatex({ texto }: Props) {
  if (!texto) return null

  // Substitui $$...$$ (bloco) e $...$ (inline) por HTML renderizado
  const partes = texto.split(/(\\$\\$[\\s\\S]+?\\$\\$|\\$[^$]+?\\$)/g)

  const html = partes.map((parte, i) => {
    if (parte.startsWith('$$') && parte.endsWith('$$')) {
      try {
        return katex.renderToString(parte.slice(2, -2), { displayMode: true, throwOnError: false })
      } catch {
        return parte
      }
    }
    if (parte.startsWith('$') && parte.endsWith('$') && parte.length > 2) {
      try {
        return katex.renderToString(parte.slice(1, -1), { displayMode: false, throwOnError: false })
      } catch {
        return parte
      }
    }
    return parte.replace(/\n/g, '<br />')
  }).join('')

  return <span dangerouslySetInnerHTML={{ __html: html }} />
}
