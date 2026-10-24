import { asDatabaseError, getDatabase, queryIslandProfile } from '../../../utils/database'

export default defineEventHandler(async (event) => {
  try {
    const id = getRouterParam(event, 'id') ?? ''
    const result = queryIslandProfile(await getDatabase(), id)
    if (!result) throw createError({ statusCode: 404, statusMessage: `Unknown island "${id}"`, data: { code: 'not_found' } })
    return result
  } catch (error) {
    throw asDatabaseError(error)
  }
})
