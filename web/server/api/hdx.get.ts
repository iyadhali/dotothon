import { asDatabaseError, getHdx } from '../utils/database'

export default defineEventHandler(async () => {
  try {
    return await getHdx()
  } catch (error) {
    throw asDatabaseError(error)
  }
})
