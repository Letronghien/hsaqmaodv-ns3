/* hsaqmaodv-rtable.h — aliases saqmaodv routing table types. */
#ifndef HSAQMAODV_RTABLE_H
#define HSAQMAODV_RTABLE_H
#include "ns3/saqmaodv-rtable.h"
namespace ns3 {
namespace hsaqmaodv {
  using RouteFlags        = saqmaodv::RouteFlags;
  using RoutingTableEntry = saqmaodv::RoutingTableEntry;
  using RoutingTable      = saqmaodv::RoutingTable;
  static constexpr auto VALID     = saqmaodv::VALID;
  static constexpr auto INVALID   = saqmaodv::INVALID;
  static constexpr auto IN_SEARCH = saqmaodv::IN_SEARCH;
} // namespace hsaqmaodv
} // namespace ns3
#endif
