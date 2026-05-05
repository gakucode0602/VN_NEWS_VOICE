package com.pmq.vnnewsvoice.article.mapper;

import com.pmq.vnnewsvoice.article.dto.CategoryDto;
import com.pmq.vnnewsvoice.article.pojo.Category;
import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface CategoryMapper {
  CategoryDto toDto(Category category);
}
