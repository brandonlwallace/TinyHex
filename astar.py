# astar.py
# A* pathfinding for hex grids (axial coordinates)
import heapq

def heuristic(a, b):
    # Manhattan distance on a hex grid
    dq = abs(a[0] - b[0])
    dr = abs(a[1] - b[1])
    ds = abs((-a[0]-a[1]) - (-b[0]-b[1]))
    return max(dq, dr, ds)

def neighbors(coord, map_coords, terrain_map=None, block_terrain=None):
    # Returns all valid neighbor hexes (not blocked)
    q, r = coord
    results = []
    for dq, dr in [ (1,0), (1,-1), (0,-1), (-1,0), (-1,1), (0,1) ]:
        nq, nr = q + dq, r + dr
        if (nq, nr) in map_coords:
            if terrain_map and block_terrain and terrain_map.get((nq, nr)) in block_terrain:
                continue
            results.append((nq, nr))
    return results

def astar(start, goal, map_coords, terrain_map=None, block_terrain=None):
    # Returns a list of axial coords from start to goal (inclusive), or [] if no path
    frontier = []
    heapq.heappush(frontier, (0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}
    while frontier:
        _, current = heapq.heappop(frontier)
        if current == goal:
            break
        for next in neighbors(current, map_coords, terrain_map, block_terrain):
            new_cost = cost_so_far[current] + 1
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost + heuristic(goal, next)
                heapq.heappush(frontier, (priority, next))
                came_from[next] = current
    # reconstruct path
    if goal not in came_from:
        return []
    path = []
    curr = goal
    while curr != start:
        path.append(curr)
        curr = came_from[curr]
    path.append(start)
    path.reverse()
    return path
