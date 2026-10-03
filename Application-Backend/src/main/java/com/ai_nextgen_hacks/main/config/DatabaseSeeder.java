package com.ai_nextgen_hacks.main.config;

import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.jdbc.core.JdbcTemplate;

@Configuration
public class DatabaseSeeder {

    @Bean
    public CommandLineRunner fixDbConstraints(JdbcTemplate jdbcTemplate) {
        return args -> {
            System.out.println("Executing SQL to fix recommendations_recommendation_type_check...");
            try {
                jdbcTemplate.execute("ALTER TABLE recommendations DROP CONSTRAINT IF EXISTS recommendations_recommendation_type_check;");
                jdbcTemplate.execute("ALTER TABLE recommendations ADD CONSTRAINT recommendations_recommendation_type_check CHECK (recommendation_type IN ('CONFIRM_AVAILABILITY', 'NO_INTERVENTION', 'REROUTE', 'EXPEDITE', 'STANDARD_NOTIFICATION'));");
                System.out.println("SQL fix executed successfully!");
            } catch (Exception e) {
                System.err.println("Error executing SQL fix: " + e.getMessage());
            }
        };
    }
}
