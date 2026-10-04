package com.ai_nextgen_hacks.main.controllers;

import com.ai_nextgen_hacks.main.dtos.DispatchPlanRequest;
import com.ai_nextgen_hacks.main.dtos.DispatchPlanResponse;
import com.ai_nextgen_hacks.main.services.DispatchService;
import com.ai_nextgen_hacks.main.services.DataIngestionService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/dispatch")
@CrossOrigin(origins = "*")
public class DispatchController {

    @Autowired
    private DispatchService dispatchService;

    @Autowired
    private DataIngestionService dataIngestionService;

    @PostMapping("/plan")
    public ResponseEntity<?> planDispatch(@RequestBody DispatchPlanRequest request) {
        try {
            DispatchPlanResponse response = dispatchService.planDispatch(request);
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(e.getMessage());
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body("An error occurred: " + e.getMessage());
        }
    }

    @PostMapping(value = "/plan-batch", consumes = "multipart/form-data")
    public ResponseEntity<?> planDispatchBatch(@RequestParam("file") org.springframework.web.multipart.MultipartFile file) {
        try {
            java.util.List<String[]> data = dataIngestionService.processFile(file);
            java.util.List<DispatchPlanResponse> responses = new java.util.ArrayList<>();
            for (String[] row : data) {
                try {
                    responses.add(dispatchService.planDispatchDynamic(row));
                } catch (Exception e) {
                    System.err.println("Error processing row: " + e.getMessage());
                }
            }
            
            // Group the responses by batch/Dispatch Unit ID for the frontend
            java.util.Map<String, java.util.List<DispatchPlanResponse>> groupedBatches = responses.stream()
                .collect(java.util.stream.Collectors.groupingBy(DispatchPlanResponse::dispatchUnitId));
                
            return ResponseEntity.ok(groupedBatches);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body("An error occurred: " + e.getMessage());
        }
    }

    @Autowired
    private com.ai_nextgen_hacks.main.repos.OrderRepository orderRepository;

    @Autowired
    private com.ai_nextgen_hacks.main.repos.DispatchUnitRepository dispatchUnitRepository;

    private final java.util.Map<String, DispatchPlanResponse> predictionCache = new java.util.concurrent.ConcurrentHashMap<>();

    @GetMapping("/data")
    public ResponseEntity<?> getDashboardData() {
        try {
            java.util.List<com.ai_nextgen_hacks.main.models.DispatchUnit> dbUnits = dispatchUnitRepository.findAll();
            java.util.List<String> unitIds = dbUnits.stream()
                    .map(com.ai_nextgen_hacks.main.models.DispatchUnit::getUnitId)
                    .collect(java.util.stream.Collectors.toList());
            if (unitIds.isEmpty()) {
                unitIds.add("DU-01");
                unitIds.add("DU-02");
            }

            java.util.List<com.ai_nextgen_hacks.main.models.Order> dbOrders = orderRepository.findAll();
            java.util.List<String[]> data = new java.util.ArrayList<>();
            int count = 0;
            for (com.ai_nextgen_hacks.main.models.Order order : dbOrders) {
                // Mock dispatch zones based on the number of drivers available so it groups perfectly
                String zone = "ZONE-" + (count % unitIds.size() + 1);
                String stops = String.valueOf(100 + (count * 2));
                String packages = String.valueOf(120 + (count * 3));
                String volume = String.valueOf(20000 + (count * 100));
                // Pass order.getStatus() as the 12th element (index 11)
                data.add(new String[]{order.getOrderId(), "DLA3", "2018-08-25", zone, "4200", stops, packages, "", volume, "600", "1", order.getStatus()});
                count++;
            }

            if (data.isEmpty()) {
                data.add(new String[]{"ORD-1042", "DLA3", "2018-08-25", "ZONE-1", "4200", "237", "304", "", "50000", "800", "1", "PENDING"});
            }

            java.util.List<DispatchPlanResponse> responses = data.stream().map(row -> {
                try {
                    String orderId = row[0];
                    DispatchPlanResponse res = predictionCache.get(orderId);
                    
                    if (res == null) {
                        res = dispatchService.planDispatchDynamic(row);
                        predictionCache.put(orderId, res);
                    }
                    
                    // Map the batch directly to the zone to ensure all products going to the same place use the same driver
                    int batchIndex = Math.abs(row[3].hashCode()) % unitIds.size();
                    String unitId = unitIds.get(batchIndex);
                    // Use the actual status from the database so user updates are visible
                    String realStatus = row.length > 11 ? row[11] : res.status();
                    return new DispatchPlanResponse(res.planningId(), realStatus, res.orderId(), unitId, res.warehouse(), res.delivery());
                } catch (Exception e) {
                    System.err.println("Error processing row: " + e.getMessage());
                    return null;
                }
            }).filter(java.util.Objects::nonNull).collect(java.util.stream.Collectors.toList());
            
            java.util.Map<String, java.util.List<DispatchPlanResponse>> groupedBatches = responses.stream()
                .collect(java.util.stream.Collectors.groupingBy(DispatchPlanResponse::dispatchUnitId));
                
            return ResponseEntity.ok(groupedBatches);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body("An error occurred: " + e.getMessage());
        }
    }

    /** Returns all orders from the DB directly — no AI processing, instant response */
    @GetMapping("/orders")
    public ResponseEntity<?> getAllOrders() {
        try {
            java.util.List<com.ai_nextgen_hacks.main.models.Order> orders = orderRepository.findAll();
            java.util.List<java.util.Map<String, Object>> result = orders.stream().map(o -> {
                java.util.Map<String, Object> map = new java.util.LinkedHashMap<>();
                map.put("orderId",     o.getOrderId());
                map.put("customerId",  o.getCustomerId());
                map.put("status",      o.getStatus());
                map.put("createdAt",   o.getCreatedAt() != null ? o.getCreatedAt().toString() : null);
                map.put("deadline",    o.getDeadline()  != null ? o.getDeadline().toString()  : null);
                return map;
            }).collect(java.util.stream.Collectors.toList());
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body("An error occurred: " + e.getMessage());
        }
    }

    /** Returns all dispatch units from the DB directly — no AI processing, instant response */
    @GetMapping("/units")
    public ResponseEntity<?> getAllUnits() {
        try {
            java.util.List<com.ai_nextgen_hacks.main.models.DispatchUnit> units = dispatchUnitRepository.findAll();
            java.util.List<java.util.Map<String, Object>> result = units.stream().map(u -> {
                java.util.Map<String, Object> map = new java.util.LinkedHashMap<>();
                map.put("unitId",          u.getUnitId());
                map.put("availability",    u.getAvailability());
                map.put("capacity",        u.getCapacity());
                map.put("currentLocation", u.getCurrentLocation());
                return map;
            }).collect(java.util.stream.Collectors.toList());
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body("An error occurred: " + e.getMessage());
        }
    }

    /**
     * Returns all DB orders grouped by their assigned dispatch unit.
     * Uses the same round-robin logic as getDashboardData — no AI processing needed.
     */
    @GetMapping("/units/assignments")
    public ResponseEntity<?> getUnitAssignments() {
        try {
            java.util.List<com.ai_nextgen_hacks.main.models.DispatchUnit> dbUnits = dispatchUnitRepository.findAll();
            java.util.List<String> unitIds = dbUnits.stream()
                    .map(com.ai_nextgen_hacks.main.models.DispatchUnit::getUnitId)
                    .sorted()
                    .collect(java.util.stream.Collectors.toList());
            if (unitIds.isEmpty()) {
                unitIds.add("DU-01");
                unitIds.add("DU-02");
            }

            java.util.List<com.ai_nextgen_hacks.main.models.Order> dbOrders = orderRepository.findAll();

            // Initialise an empty list for every unit so units with no orders still appear
            java.util.Map<String, java.util.List<java.util.Map<String, Object>>> result = new java.util.LinkedHashMap<>();
            for (String uid : unitIds) result.put(uid, new java.util.ArrayList<>());

            int count = 0;
            for (com.ai_nextgen_hacks.main.models.Order order : dbOrders) {
                // Replicate the same zone → unit assignment used in getDashboardData
                String zone = "ZONE-" + (count % unitIds.size() + 1);
                int batchIndex = Math.abs(zone.hashCode()) % unitIds.size();
                String assignedUnit = unitIds.get(batchIndex);

                java.util.Map<String, Object> map = new java.util.LinkedHashMap<>();
                map.put("orderId",     order.getOrderId());
                map.put("customerId",  order.getCustomerId());
                map.put("status",      order.getStatus());
                map.put("createdAt",   order.getCreatedAt() != null ? order.getCreatedAt().toString() : null);
                map.put("deadline",    order.getDeadline()  != null ? order.getDeadline().toString()  : null);
                map.put("dispatchUnit", assignedUnit);
                result.get(assignedUnit).add(map);
                count++;
            }
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body("An error occurred: " + e.getMessage());
        }
    }
}
