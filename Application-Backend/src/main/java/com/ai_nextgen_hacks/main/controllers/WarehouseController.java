package com.ai_nextgen_hacks.main.controllers;

import com.ai_nextgen_hacks.main.services.DataIngestionService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/warehouse")
public class WarehouseController {

    @Autowired
    private DataIngestionService dataIngestionService;

    @PostMapping("/upload")
    public ResponseEntity<?> uploadDataset(@RequestParam("file") MultipartFile file) {
        try {
            List<String[]> extractedData = dataIngestionService.processFile(file);
            return ResponseEntity.ok(Map.of(
                "message", "File uploaded and processed successfully.",
                "rowsProcessed", extractedData.size(),
                "status", "LEGITIMATE"
            ));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of("error", "Failed to process file: " + e.getMessage()));
        }
    }

    @PostMapping("/simulations")
    public ResponseEntity<String> runSimulation() {
        return ResponseEntity.accepted().body("{\"message\": \"Simulation started\", \"jobId\": \"JOB-" + System.currentTimeMillis() + "\"}");
    }

    @PostMapping("/picking/rank")
    public ResponseEntity<String> retrieveTaskRanking() {
        return ResponseEntity.ok("{\"taskId\": \"TASK-9021\", \"priority\": \"HIGH\", \"status\": \"RECOMMENDED\"}");
    }
}
