import { asDatabaseError, getDatabase, queryEconomics } from '../utils/database'

export default defineEventHandler(async () => {
  try {
    return queryEconomics(await getDatabase())
  } catch (error) {
    throw asDatabaseError(error)
  }
})
