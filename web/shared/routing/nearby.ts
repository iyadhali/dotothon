/**
 * Island access report: for one origin island, the nearest reachable facilities in each
 * category with travel time, fare and whether the trip home is possible the same day.
 *
 * Pure and browser-safe; built on `planNearestDestinations` and `planIslandToIsland`.
 */
import { planIslandToIsland, planNearestDestinations } from './router.ts'
import { estimateJourneyCost, type FareTable, type JourneyCost, type Traveller } from './cost.ts'
import type { Journey, MultimodalNetwork, NetworkSelection, OriginAccessStatus } from './types'

export interface AccessReportOptions extends NetworkSelection {
  originIslandId: string
  departureMinute: number
  categories: string[]
  /** Destinations per category. */
  limit?: number
  /** Time spent at the facility before heading home. */
  appointmentMinutes?: number
  /** Lodging and meals for one night away, MVR. Omitted means overnight cost is unknown. */
  overnightMvr?: number
  /** Fare rules to apply (concessions, emergency). Defaults to an adult resident. */
  traveller?: Traveller
}

export interface DestinationAccess {
  journey: Journey
  cost: JourneyCost
  /** Trip home after the appointment; null when no itinerary exists within 24 h. */
  returnJourney: Journey | null
  returnCost: JourneyCost | null
  /** Home again before midnight on the travel day. */
  sameDayReturn: boolean
  /** Known fares both ways plus one night away when the return is not same-day. */
  roundTripMvr: number
  /** Some leg (or the overnight stay) has no price, so `roundTripMvr` is a lower bound. */
  roundTripPartial: boolean
}

export interface CategoryAccess {
  category: string
  status: OriginAccessStatus
  destinations: DestinationAccess[]
}

const DAY_MINUTES = 24 * 60

export function buildAccessReport(
  network: MultimodalNetwork,
  fares: FareTable | null,
  options: AccessReportOptions,
): CategoryAccess[] {
  const selection: NetworkSelection = {
    allowedModes: options.allowedModes,
    disabledRouteIds: options.disabledRouteIds,
    disabledServiceIds: options.disabledServiceIds,
    dayOfWeek: options.dayOfWeek,
  }
  const appointment = options.appointmentMinutes ?? 120
  const emptyFares: FareTable = fares ?? {
    schemaVersion: 1,
    currency: 'MVR',
    usdMvr: 15.42,
    generatedAt: '',
    airRoutes: {},
    seaDetour: 1.1,
    notes: [],
  }

  return options.categories.map((category) => {
    const plan = planNearestDestinations(
      network,
      { ...selection, originIslandId: options.originIslandId, departureMinute: options.departureMinute, category },
      options.limit ?? 3,
    )
    const destinations = plan.journeys.map((journey): DestinationAccess => {
      const cost = estimateJourneyCost(network, emptyFares, journey, options.traveller)
      if (journey.elapsedMinutes === 0) {
        return {
          journey,
          cost,
          returnJourney: journey,
          returnCost: cost,
          sameDayReturn: true,
          roundTripMvr: 0,
          roundTripPartial: false,
        }
      }
      const leaveFacility = journey.arrivalMinute + appointment
      const returnJourney = planIslandToIsland(network, {
        ...selection,
        fromIslandId: journey.destinationIslandId,
        toIslandId: options.originIslandId,
        departureMinute: leaveFacility,
        allowNextDay: true,
      })
      const returnCost = returnJourney ? estimateJourneyCost(network, emptyFares, returnJourney, options.traveller) : null
      const sameDayReturn =
        returnJourney !== null && journey.dayOffset === 0 && returnJourney.arrivalMinute < DAY_MINUTES
      const overnight = !sameDayReturn
      // Aasandha pays emergency transport; an escort's night away is still counted.
      const nightCost = overnight ? (options.overnightMvr ?? null) : 0
      const roundTripMvr = cost.knownMvr + (returnCost?.knownMvr ?? cost.knownMvr) + (nightCost ?? 0)
      const roundTripPartial =
        !cost.complete || (returnCost ? !returnCost.complete : true) || (overnight && nightCost === null)
      return { journey, cost, returnJourney, returnCost, sameDayReturn, roundTripMvr, roundTripPartial }
    })
    return { category, status: plan.status, destinations }
  })
}
