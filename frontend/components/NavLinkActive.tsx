'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

interface Props {
  href: string
  label: string
  icon: React.ReactNode
}

export default function NavLinkActive({ href, label, icon }: Props) {
  const pathname = usePathname()
  const active = href === '/' ? pathname === '/' : pathname.startsWith(href)

  return (
    <Link
      href={href}
      className={`flex items-center gap-1.5 text-[13px] font-medium transition nav-underline ${
        active
          ? 'text-[#D4A853]'
          : 'text-[#9E9589] hover:text-[#F2EDE4]'
      }`}
      data-active={active}
    >
      {icon}
      {label}
    </Link>
  )
}
