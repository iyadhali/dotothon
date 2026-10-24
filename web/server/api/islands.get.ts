import { asDatabaseError, getIslands } from '../utils/database'

export default defineEventHandler(async (event) => {
  try {
    const collection = await getIslands()
    setResponseHeader(event, 'content-type', 'application/geo+json; charset=utf-8')
    return collection
  } catch (error) {
    throw asDatabaseError(error)
  }
})
