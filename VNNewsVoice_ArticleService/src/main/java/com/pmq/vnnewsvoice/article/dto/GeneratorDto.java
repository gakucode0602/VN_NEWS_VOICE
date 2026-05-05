package com.pmq.vnnewsvoice.article.dto;

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
public class GeneratorDto {
  private Long id;
  private String name;
  private String logoUrl;
  private String url;
  private Boolean isActive;
}
