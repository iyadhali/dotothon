import { asDatabaseError, getDatabase, querySeaLinks } from '../utils/database'

export default defineEventHandler(async (event) => {
  try {
    const { island } = getQuery(event)
    return querySeaLinks(await getDatabase(), typeof island === 'string' && island ? island : undefined)
  } catch (error) {
    throw asDatabaseError(error)
  }
})
