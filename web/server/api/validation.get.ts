import { asDatabaseError, getDatabase, queryValidation } from '../utils/database'

export default defineEventHandler(async () => {
  try {
    return queryValidation(await getDatabase())
  } catch (error) {
    throw asDatabaseError(error)
  }
})
