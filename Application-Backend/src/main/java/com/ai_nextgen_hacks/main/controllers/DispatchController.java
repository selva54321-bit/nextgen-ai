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

    @GetMapping("/data")
    public ResponseEntity<?> getDashboardData() {
        try {
            java.util.List<String[]> data = new java.util.ArrayList<>();
            data.add(new String[]{"ORD-1042", "DLA3", "2018-08-25", "RC-01", "4200", "237", "304", "", "50000", "800", "1"});
            data.add(new String[]{"ORD-2091", "DLA3", "2018-08-25", "RC-01", "4200", "150", "200", "", "30000", "600", "1"});
            data.add(new String[]{"ORD-3310", "DLA3", "2018-08-25", "RC-02", "4200", "100", "150", "", "20000", "400", "0"});
            data.add(new String[]{"ORD-4102", "DLA3", "2018-08-25", "RC-02", "4200", "50", "80", "", "10000", "300", "0"});

            java.util.List<DispatchPlanResponse> responses = new java.util.ArrayList<>();
            for (String[] row : data) {
                try {
                    DispatchPlanResponse res = dispatchService.planDispatchDynamic(row);
                    String unitId = (row[0].equals("ORD-1042") || row[0].equals("ORD-2091")) ? "DU-01" : "DU-02";
                    responses.add(new DispatchPlanResponse(res.planningId(), res.status(), res.orderId(), unitId, res.warehouse(), res.delivery()));
                } catch (Exception e) {
                    System.err.println("Error processing row: " + e.getMessage());
                }
            }
            
            java.util.Map<String, java.util.List<DispatchPlanResponse>> groupedBatches = responses.stream()
                .collect(java.util.stream.Collectors.groupingBy(DispatchPlanResponse::dispatchUnitId));
                
            return ResponseEntity.ok(groupedBatches);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body("An error occurred: " + e.getMessage());
        }
    }
}
