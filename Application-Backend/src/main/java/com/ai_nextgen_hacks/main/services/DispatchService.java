package com.ai_nextgen_hacks.main.services;

import com.ai_nextgen_hacks.main.dtos.DispatchPlanRequest;
import com.ai_nextgen_hacks.main.dtos.DispatchPlanResponse;
import com.ai_nextgen_hacks.main.models.DispatchAssignment;
import com.ai_nextgen_hacks.main.models.DispatchUnit;
import com.ai_nextgen_hacks.main.models.Order;
import com.ai_nextgen_hacks.main.repos.DispatchAssignmentRepository;
import com.ai_nextgen_hacks.main.repos.DispatchUnitRepository;
import com.ai_nextgen_hacks.main.repos.OrderRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.http.ResponseEntity;

@Service
public class DispatchService {

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private DispatchUnitRepository dispatchUnitRepository;

    @Autowired
    private DispatchAssignmentRepository dispatchAssignmentRepository;

    @Autowired
    private RestTemplate restTemplate;

    // FastAPI URLs (mocked for now, can be moved to application.properties)
    private final String warehouseEngineUrl = "http://10.10.67.253:9000/v1/priorities/rank";
    private final String deliveryEngineUrl = "http://10.10.67.253:8000/predict";

    public DispatchPlanResponse planDispatch(DispatchPlanRequest request) {
        String planningId = "PLAN-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();
        
        // 1. Validate request (checking first order for simplicity)
        String orderId = request.orderIds().isEmpty() ? null : request.orderIds().get(0);
        Order order = orderRepository.findById(orderId).orElse(null);
        DispatchUnit unit = dispatchUnitRepository.findById(request.dispatchUnitId()).orElse(null);

        if (order == null || unit == null) {
            throw new IllegalArgumentException("Invalid order or dispatch unit ID");
        }

        // 2. Call Warehouse FastAPI (Actual integration logic)
        boolean isDispatchReady = false;
        String pickingStatus = "PENDING";
        
        try {
            Map<String, Object> pickerPos = Map.of("x", 0.0, "y", 0.0, "z", 1.0);
            
            // Mock a task for the order to rank
            Map<String, Object> task1 = Map.of(
                "task_id", "T-" + orderId,
                "dispatch_id", request.dispatchUnitId(),
                "location", "RC-01",
                "x", 10.0,
                "y", 20.0,
                "z", 1.0,
                "remaining_quantity", 5,
                "deadline", LocalDateTime.now().plusHours(1).toString()
            );

            Map<String, Object> configWeights = Map.of(
                "urgency", 0.40,
                "quantity", 0.25,
                "complexity", 0.20,
                "distance", 0.15
            );

            Map<String, Object> config = Map.of(
                "sla_minutes", 90.0,
                "picker_speed_mps", 1.2,
                "unit_pick_time_sec", 5.0,
                "coord_unit_to_meters", 1.0,
                "z_weight", 1.0,
                "tier_urgent_max_slack_min", 15.0,
                "tier_high_max_slack_min", 30.0,
                "slack_horizon_min", 90.0,
                "weights", configWeights
            );

            Map<String, Object> warehouseReq = Map.of(
                "now", LocalDateTime.now().toString(),
                "picker_position", pickerPos,
                "tasks", List.of(task1),
                "config", config
            );

            ResponseEntity<Map> warehouseResp = restTemplate.postForEntity(warehouseEngineUrl, warehouseReq, Map.class);
            
            if (warehouseResp.getStatusCode().is2xxSuccessful() && warehouseResp.getBody() != null) {
                Map<String, Object> body = warehouseResp.getBody();
                if (body.containsKey("next_task") && body.get("next_task") != null) {
                    Map<String, Object> nextTask = (Map<String, Object>) body.get("next_task");
                    pickingStatus = "NEXT TASK PRIORITY: " + nextTask.getOrDefault("priority_level", "NORMAL");
                    // We'll consider it ready for dispatch in our prototype flow just to continue the ML delivery test
                    isDispatchReady = true; 
                } else {
                    pickingStatus = "NO_TASKS";
                    isDispatchReady = true;
                }
            } else {
                pickingStatus = "COMPLETED"; // Fallback for prototype
                isDispatchReady = true;
            }
        } catch (Exception e) {
            // Log error and use fallback for hackathon demonstration if engine is down
            System.err.println("Failed to reach Warehouse Engine: " + e.getMessage());
            pickingStatus = "COMPLETED";
            isDispatchReady = true;
        }
        
        if (!isDispatchReady) {
            return new DispatchPlanResponse(
                planningId, "PENDING_WAREHOUSE", orderId, unit.getUnitId(),
                new DispatchPlanResponse.WarehouseInfo(pickingStatus, false),
                null
            );
        }

        // 3. Create Dispatch Assignment
        DispatchAssignment assignment = new DispatchAssignment();
        assignment.setOrderId(orderId);
        assignment.setUnitId(unit.getUnitId());
        assignment.setAssignedAt(LocalDateTime.now());
        assignment.setStatus("PROCESSING");
        dispatchAssignmentRepository.save(assignment);

        // 4. Call Delivery ML FastAPI (Actual integration logic)
        Double failureProbability = 0.0;
        String riskBand = "UNKNOWN";
        List<String> topFactors = List.of();
        
        try {
            Map<String, Object> routeData = Map.of(
                "station_code", "3313071",
                "date", "2018-08-26",
                "executor_capacity_cm3", 160000.0,
                "stops", 259,
                "route_num_packages", 19
            );

            Map<String, Object> packageDim = Map.of(
                "depth_cm", 30.0,
                "width_cm", 20.0,
                "height_cm", 15.0
            );
            
            Map<String, Object> timeWindow = Map.of(
                "start_time_utc", "2018-08-26T07:00:00Z",
                "end_time_utc", "2018-08-26T08:00:00Z"
            );

            Map<String, Object> pkg = Map.of(
                "dimensions", packageDim,
                "planned_service_time_seconds", 644.099999,
                "time_window", timeWindow
            );

            Map<String, Object> stopData = Map.of(
                "zone_id", "C-7.3E",
                "packages", List.of(pkg)
            );

            Map<String, Object> deliveryReq = Map.of(
                "route", routeData,
                "stop", stopData
            );
            
            ResponseEntity<Map> deliveryResp = restTemplate.postForEntity(deliveryEngineUrl, deliveryReq, Map.class);
            
            if (deliveryResp.getStatusCode().is2xxSuccessful() && deliveryResp.getBody() != null) {
                Map<String, Object> body = deliveryResp.getBody();
                if (body.containsKey("failure_probability")) {
                    failureProbability = Double.parseDouble(body.get("failure_probability").toString());
                }
                if (body.containsKey("risk_band")) {
                    riskBand = body.get("risk_band").toString();
                }
                if (body.containsKey("top_factors")) {
                    List<Map<String, Object>> factorsObj = (List<Map<String, Object>>) body.get("top_factors");
                    List<String> parsedFactors = new ArrayList<>();
                    for (Map<String, Object> factorMap : factorsObj) {
                        parsedFactors.add(factorMap.getOrDefault("factor", "unknown").toString());
                    }
                    topFactors = parsedFactors;
                }
            } else {
                // Fallback for prototype
                failureProbability = 0.072;
                riskBand = "HIGH";
                topFactors = List.of("route_num_stops", "total_service_time", "has_time_window");
            }
        } catch (Exception e) {
            System.err.println("Failed to reach Delivery ML Engine: " + e.getMessage());
            // Fallback for prototype if ML API is not running
            failureProbability = 0.072;
            riskBand = "HIGH";
            topFactors = List.of("route_num_stops", "total_service_time", "has_time_window");
        }

        // Business logic based on ML prediction
        if (riskBand.equals("HIGH") || failureProbability > 0.05) {
            assignment.setStatus("READY_FOR_CONFIRMATION"); // Needs human/customer intervention
        } else {
            assignment.setStatus("DISPATCH_APPROVED"); // Low risk, proceed automatically
        }
        dispatchAssignmentRepository.save(assignment);

        return new DispatchPlanResponse(
            planningId,
            assignment.getStatus(),
            orderId,
            unit.getUnitId(),
            new DispatchPlanResponse.WarehouseInfo(pickingStatus, isDispatchReady),
            new DispatchPlanResponse.DeliveryInfo(failureProbability, riskBand, topFactors)
        );
    }
}
