package com.ai_nextgen_hacks.main.services;

import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVRecord;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.InputStreamReader;
import java.io.Reader;
import java.util.ArrayList;
import java.util.List;

@Service
public class DataIngestionService {

    public List<String[]> processFile(MultipartFile file) throws Exception {
        String filename = file.getOriginalFilename();
        if (filename == null) {
            throw new IllegalArgumentException("File name is missing.");
        }

        List<String[]> extractedData = new ArrayList<>();

        if (filename.endsWith(".csv")) {
            extractedData = processCsv(file);
        } else if (filename.endsWith(".xlsx") || filename.endsWith(".xls")) {
            extractedData = processExcel(file);
        } else {
            throw new IllegalArgumentException("Unsupported file format. Please upload a CSV or Excel file.");
        }

        // Verify Legitimacy
        verifyDataLegitimacy(extractedData);

        return extractedData;
    }

    private List<String[]> processCsv(MultipartFile file) throws Exception {
        List<String[]> data = new ArrayList<>();
        try (Reader reader = new InputStreamReader(file.getInputStream());
             CSVParser csvParser = new CSVParser(reader, CSVFormat.DEFAULT.withFirstRecordAsHeader())) {
            
            for (CSVRecord csvRecord : csvParser) {
                String[] row = new String[csvRecord.size()];
                for (int i = 0; i < csvRecord.size(); i++) {
                    row[i] = csvRecord.get(i);
                }
                data.add(row);
            }
        }
        return data;
    }

    private List<String[]> processExcel(MultipartFile file) throws Exception {
        List<String[]> data = new ArrayList<>();
        try (Workbook workbook = new XSSFWorkbook(file.getInputStream())) {
            Sheet sheet = workbook.getSheetAt(0);
            boolean firstRow = true;
            for (Row row : sheet) {
                if (firstRow) {
                    firstRow = false; // Skipping header
                    continue;
                }
                List<String> rowData = new ArrayList<>();
                for (Cell cell : row) {
                    switch (cell.getCellType()) {
                        case STRING -> rowData.add(cell.getStringCellValue());
                        case NUMERIC -> rowData.add(String.valueOf(cell.getNumericCellValue()));
                        case BOOLEAN -> rowData.add(String.valueOf(cell.getBooleanCellValue()));
                        default -> rowData.add("");
                    }
                }
                data.add(rowData.toArray(new String[0]));
            }
        }
        return data;
    }

    private void verifyDataLegitimacy(List<String[]> data) {
        if (data == null || data.isEmpty()) {
            throw new IllegalArgumentException("The uploaded file contains no data rows.");
        }
        
        for (int i = 0; i < data.size(); i++) {
            String[] row = data.get(i);
            
            if (row.length == 0 || (row.length == 1 && row[0].trim().isEmpty())) {
                throw new IllegalArgumentException("Row " + (i + 1) + " is empty or malformed.");
            }

            // Simple legitimacy check: require the first column (e.g. Order ID or Product ID) to not be null/empty
            if (row[0] == null || row[0].trim().isEmpty()) {
                 throw new IllegalArgumentException("Validation Error at row " + (i + 1) + ": Missing primary identifier in first column.");
            }
        }
    }
}
