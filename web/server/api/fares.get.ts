import { asDatabaseError, getDatabase, queryFares } from '../utils/database'

export default defineEventHandler(async () => {
  try {
    return queryFares(await getDatabase())
  } catch (error) {
    throw asDatabaseError(error)
  }
})
