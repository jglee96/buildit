import { createBrowserRouter } from 'react-router-dom'
import { PlannerPage } from '@/pages/planner'
import { ResultPage } from '@/pages/result'
import { RouteError } from '@/app/providers/route-error'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <PlannerPage />,
    errorElement: <RouteError />
  },
  {
    path: '/results/:runId',
    element: <ResultPage />,
    errorElement: <RouteError />
  }
])
