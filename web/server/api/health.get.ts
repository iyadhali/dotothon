import { asDatabaseError, getDatabaseStats } from '../utils/database'

export default defineEventHandler(async () => {
  try {
    const database = await getDatabaseStats()
    return {
      status: 'ok',
      application: 'maldives-mobility',
      database: { available: true, ...database },
    }
  } catch (error) {
    throw asDatabaseError(error)
  }
})
