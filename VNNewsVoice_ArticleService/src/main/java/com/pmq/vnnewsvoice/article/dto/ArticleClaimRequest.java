package com.pmq.vnnewsvoice.article.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ArticleClaimRequest {
  private String sourceId;
  private String sourceName;
  private String title;

  @NotBlank(message = "url is required")
  private String url;
}
