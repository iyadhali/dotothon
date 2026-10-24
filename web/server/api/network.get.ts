import { asDatabaseError, getNetwork } from '../utils/database'

export default defineEventHandler(async () => {
  try {
    return await getNetwork()
  } catch (error) {
    throw asDatabaseError(error)
  }
})
