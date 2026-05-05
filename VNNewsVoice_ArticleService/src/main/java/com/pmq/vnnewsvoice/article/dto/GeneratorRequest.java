package com.pmq.vnnewsvoice.article.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class GeneratorRequest {
  @NotBlank(message = "Tên cấu hình crawler không được để trống")
  private String name;

  private String logoUrl;

  @NotBlank(message = "URL trang web không được để trống")
  private String url;

  private String rssUrl;
  private Boolean isActive;
  private Integer crawlIntervalMinutes;
}
