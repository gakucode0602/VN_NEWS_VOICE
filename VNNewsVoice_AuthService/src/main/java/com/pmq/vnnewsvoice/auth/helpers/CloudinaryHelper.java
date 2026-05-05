package com.pmq.vnnewsvoice.auth.helpers;

import com.cloudinary.Cloudinary;
import com.cloudinary.utils.ObjectUtils;
import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

@Component
@RequiredArgsConstructor
public class CloudinaryHelper {

  private final Cloudinary cloudinary;

  public Map<String, String> uploadMultipartFile(MultipartFile file) throws IOException {
    try {
      Map res =
          cloudinary.uploader().upload(file.getBytes(), ObjectUtils.asMap("resource_type", "auto"));
      Map<String, String> result = new HashMap<>();
      result.put("url", res.get("secure_url").toString());
      result.put("publicId", res.get("public_id").toString());
      return result;
    } catch (IOException e) {
      throw new IOException("Lỗi upload file lên cloud");
    }
  }

  public Map<String, String> uploadFile(File file) throws IOException {
    try {
      Map res = cloudinary.uploader().upload(file, ObjectUtils.asMap("resource_type", "auto"));
      Map<String, String> result = new HashMap<>();
      result.put("url", res.get("secure_url").toString());
      result.put("publicId", res.get("public_id").toString());
      return result;
    } catch (IOException e) {
      throw new IOException("Lỗi upload lên cloud");
    }
  }

  public boolean deleteFile(String publicId) throws IOException {
    try {
      Map res = cloudinary.uploader().destroy(publicId, ObjectUtils.emptyMap());
      return !res.get("result").toString().equals("not found");
    } catch (Exception e) {
      throw new IOException("Lỗi xóa file trên cloud");
    }
  }
}
