import { Link, NavLink } from 'react-router-dom'

const links = [
  { to: '/', label: 'Ingredients' },
  { to: '/verification', label: 'Verify' },
  { to: '/combinations', label: 'Generate' },
  { to: '/recipes', label: 'Recipes' },
]

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-stone-200/90 bg-cream-50/95 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:py-5">
          <Link to="/" className="group">
            <span className="font-serif text-xl text-stone-900 group-hover:text-sage-700">Beverage Knowledge Base</span>
            <span className="mt-0.5 block text-xs text-stone-500">Personal ingredient & recipe library</span>
          </Link>
          <nav className="flex flex-wrap gap-1">
            {links.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end={l.to === '/'}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-sage-600 text-white shadow-sm shadow-sage-600/20'
                      : 'text-stone-600 hover:bg-cream-200 hover:text-stone-900'
                  }`
                }
              >
                {l.label}
              </NavLink>
            ))}
            <NavLink
              to="/recipes/new"
              className={({ isActive }) =>
                `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive ? 'bg-terracotta-500 text-white' : 'text-terracotta-500 hover:bg-terracotta-soft'
                }`
              }
            >
              + New recipe
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8 sm:py-10">{children}</main>
      <footer className="border-t border-stone-200/80 py-6 text-center text-xs text-stone-400">
        Verified knowledge only in default views · Unverified data always labeled
      </footer>
    </div>
  )
}
