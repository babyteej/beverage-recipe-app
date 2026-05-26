import { Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import CombinationGenerator from './pages/CombinationGenerator'
import IngredientBrowser from './pages/IngredientBrowser'
import IngredientDetail from './pages/IngredientDetail'
import IngredientEdit from './pages/IngredientEdit'
import RecipeBuilder from './pages/RecipeBuilder'
import RecipeBrowser from './pages/RecipeBrowser'
import RecipeDetail from './pages/RecipeDetail'
import VerificationQueue from './pages/VerificationQueue'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<IngredientBrowser />} />
        <Route path="/ingredients/:id" element={<IngredientDetail />} />
        <Route path="/ingredients/:id/edit" element={<IngredientEdit />} />
        <Route path="/verification" element={<VerificationQueue />} />
        <Route path="/combinations" element={<CombinationGenerator />} />
        <Route path="/recipes" element={<RecipeBrowser />} />
        <Route path="/recipes/new" element={<RecipeBuilder />} />
        <Route path="/recipes/:id" element={<RecipeDetail />} />
        <Route path="/recipes/:id/edit" element={<RecipeBuilder />} />
      </Routes>
    </Layout>
  )
}
