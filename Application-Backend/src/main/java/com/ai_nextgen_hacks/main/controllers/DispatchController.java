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
}
