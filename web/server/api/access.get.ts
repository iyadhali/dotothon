import { asDatabaseError, getDatabase, queryAccess } from '../utils/database'

export default defineEventHandler(async (event) => {
  try {
    const query = getQuery(event)
    const category = typeof query.category === 'string' ? query.category : ''
    const departure = Number(query.departure ?? 480)
    const air =
      query.estimatedAir === undefined ? undefined : query.estimatedAir === '1' || query.estimatedAir === 'true' ? 1 : 0
    return queryAccess(await getDatabase(), category, departure, air)
  } catch (error) {
    throw asDatabaseError(error)
  }
})
