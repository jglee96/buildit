import { RouterProvider } from 'react-router-dom'
import { router } from '@/app/providers/router'

export function App(): JSX.Element {
  return <RouterProvider router={router} />
}
