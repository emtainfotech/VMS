<!-- Single Modal Form -->
<div class="modal modal-blur fade" id="modal-candidate" tabindex="-1" role="dialog" aria-hidden="true">
  <div class="modal-dialog modal-lg modal-dialog-scrollable" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Candidate Profile</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body" style="overflow-y: auto; max-height: calc(100vh - 200px);">
        <form id="candidateForm" method="POST" enctype="multipart/form-data" novalidate>
          {% csrf_token %}
          
          <!-- Personal Information Section -->
          <h5 class="text-secondary mb-4">Personal Information</h5>
          <div class="row">
            <div class="col-md-6 mb-3">
              <label class="form-label">Candidate Name <span class="text-danger">*</span></label>
              <input type="text" class="form-control" name="candidate_name" 
                     value="{{ candidate.candidate_name }}" 
                     required minlength="2" maxlength="100"
                     pattern="^[a-zA-Z\s]*$" />
              <div class="invalid-feedback">
                Please enter a valid name (2-100 characters, letters only)
              </div>
            </div>
            
            <div class="col-md-6 mb-3">
              <label class="form-label">Mobile Number <span class="text-danger">*</span></label>
              <input type="tel" class="form-control" name="candidate_mobile_number" 
                     value="{{ candidate.candidate_mobile_number }}" 
                     required pattern="[0-9]{10}" 
                     maxlength="10" />
              <div class="invalid-feedback">
                Please enter a valid 10-digit mobile number
              </div>
            </div>
            
            <div class="col-md-6 mb-3">
              <label class="form-label">Email Address</label>
              <input type="email" class="form-control" name="candidate_email_address" 
                     value="{{ candidate.candidate_email_address }}" 
                     maxlength="100" pattern="^[^\s@]+@[^\s@]+\.[^\s@]+$"/>
              <div class="invalid-feedback">
                Please enter a valid email address
              </div>
            </div>
            
            <div class="col-md-6 mb-3">
              <label class="form-label">Gender <span class="text-danger">*</span></label>
              <select class="form-select" name="gender" required>
                <option value="" disabled>Select Gender</option>
                <option value="Male" {% if candidate.gender == "Male" %}selected{% endif %}>Male</option>
                <option value="Female" {% if candidate.gender == "Female" %}selected{% endif %}>Female</option>
                <option value="Other" {% if candidate.gender == "Other" %}selected{% endif %}>Other</option>
              </select>
              <div class="invalid-feedback">
                Please select gender
              </div>
            </div>
            
            <div class="col-md-6 mb-3">
              <label class="form-label">Profile Photo</label>
              <input type="file" class="form-control" name="candidate_photo" 
                     accept="image/*" />
              <div class="invalid-feedback">
                Please upload a valid image (JPEG, PNG, JPG)
              </div>
              <small class="text-muted">Max size: 10MB</small>
            </div>
            
            <div class="col-md-6 mb-3">
              <label class="form-label">Resume <span class="text-danger">*</span></label>
              <input type="file" class="form-control" name="candidate_resume" 
                     accept=".pdf,.doc,.docx" />
              <div class="invalid-feedback">
                Please upload a valid resume (PDF, DOC, DOCX)
              </div>
              <small class="text-muted">Max size: 10MB (PDF, DOC, DOCX)</small>
            </div>
            
            <div class="col-md-6 mb-3">
              <label class="form-label">Lead Source</label>
              <select name="lead_source" class="form-select" required id="leadSourceSelect">
                  <option value="" disabled selected>Select Lead Source</option>
                  <option value="EVMS" {% if candidate.lead_source == "EVMS" %}selected{% endif %}>EVMS</option>
                  <option value="Walk-In" {% if candidate.lead_source == "Walk-In" %}selected{% endif %}>Walk-In</option>
                  <option value="Job Hai" {% if candidate.lead_source == "Job Hai" %}selected{% endif %}>Job Hai</option>
                  <option value="Naukari" {% if candidate.lead_source == "Naukari" %}selected{% endif %}>Naukari</option>
                  <option value="Apna" {% if candidate.lead_source == "Apna" %}selected{% endif %}>Apna</option>
                  <option value="Expertia" {% if candidate.lead_source == "Expertia" %}selected{% endif %}>Expertia</option>
                  <option value="Instagram" {% if candidate.lead_source == "Instagram" %}selected{% endif %}>Instagram</option>
                  <option value="Website" {% if candidate.lead_source == "Website" %}selected{% endif %}>Website</option>
                  <option value="Indeed" {% if candidate.lead_source == "Indeed" %}selected{% endif %}>Indeed</option>
                  <option value="Facebook" {% if candidate.lead_source == "Facebook" %}selected{% endif %}>Facebook</option>
                  <option value="Linkedin" {% if candidate.lead_source == "Linkedin" %}selected{% endif %}>Linkedin</option>
                  <option value="Personal Refference" {% if candidate.lead_source == "Personal Refference" %}selected{% endif %}>Personal Refference</option>
                  <option value="Other" {% if candidate.lead_source == "Other" %}selected{% endif %}>Other</option>
              </select>
              <div id="otherLeadSourceContainer" style="display: none;" class="mt-2">
                <label class="form-label">Specify Other Lead Source</label>
                <input type="text" class="form-control" name="other_lead_source" 
                       value="{{ candidate.other_lead_source }}" maxlength="100">
              </div>
            </div>
          </div>
          
          <!-- Candidate Details Section -->
          <hr class="my-4">
          <h5 class="text-secondary mb-4">Candidate Information</h5>
          <div class="row">
            <div class="col-md-6 mb-3">
              <label class="form-label">Alternate Mobile Number</label>
              <input type="tel" class="form-control" name="candidate_alternate_mobile_number" 
                     value="{{candidate.candidate_alternate_mobile_number}}"
                     pattern="[0-9]{10}" maxlength="10">
              <div class="invalid-feedback">
                Please enter a valid 10-digit mobile number
              </div>
            </div>
            
<div class="col-md-6 mb-3">
  <label class="form-label">Preferred Location</label>
  <div class="dropdown">
    <button class="btn btn-outline-secondary dropdown-toggle w-100 text-start" type="button" 
            id="locationDropdown" data-bs-toggle="dropdown" aria-expanded="false">
      {% if candidate.preferred_location %}
        {% if candidate.preferred_location|length > 2 %}
          {{ candidate.preferred_location|length }} locations selected
        {% else %}
          {{ candidate.preferred_location|join:", " }}
        {% endif %}
      {% else %}
        Select locations...
      {% endif %}
    </button>
    <ul class="dropdown-menu w-100 p-2" aria-labelledby="locationDropdown">
      <!-- Search Box -->
      <li>
        <div class="px-2 mb-2">
          <input type="text" class="form-control search-input" 
                 placeholder="Search locations..." 
                 id="locationSearch">
        </div>
      </li>
      <!-- Options List -->
      <div class="dropdown-options" style="max-height: 250px; overflow-y: auto;">
        {% for district in districts %}
        <li class="dropdown-item">
          <div class="form-check">
            <input class="form-check-input" type="checkbox" name="preferred_location" 
                   value="{{ district }}" id="loc-{{ forloop.counter }}"
                   {% if district in candidate.preferred_location %}checked{% endif %}>
            <label class="form-check-label w-100" for="loc-{{ forloop.counter }}">
              {{ district }}
            </label>
          </div>
        </li>
        {% endfor %}
      </div>
    </ul>
  </div>
  <div class="invalid-feedback">
    Please select at least one location
  </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
  const locationDropdown = document.getElementById('locationDropdown');
  const locationCheckboxes = document.querySelectorAll('input[name="preferred_location"]');
  const locationSearch = document.getElementById('locationSearch');
  const dropdownOptions = document.querySelector('.dropdown-options');
  
  // Update button text when selections change
  locationCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', updateLocationButtonText);
  });
  
  function updateLocationButtonText() {
    const selectedItems = Array.from(document.querySelectorAll('input[name="preferred_location"]:checked'))
      .map(cb => cb.nextElementSibling.textContent);
    
    if (selectedItems.length === 0) {
      locationDropdown.textContent = 'Select locations...';
    } else if (selectedItems.length > 2) {
      locationDropdown.textContent = selectedItems.length + ' locations selected';
    } else {
      locationDropdown.textContent = selectedItems.join(', ');
    }
  }
  
  // Search functionality
  locationSearch.addEventListener('input', function() {
    const searchTerm = this.value.toLowerCase();
    const options = dropdownOptions.querySelectorAll('.dropdown-item');
    
    options.forEach(option => {
      const text = option.textContent.toLowerCase();
      if (text.includes(searchTerm)) {
        option.style.display = 'block';
      } else {
        option.style.display = 'none';
      }
    });
  });
  
  // Keep dropdown open when clicking on checkboxes or search box
  document.querySelectorAll('.dropdown-menu input, .dropdown-menu label').forEach(element => {
    element.addEventListener('click', function(e) {
      e.stopPropagation();
    });
  });
});
</script>

<style>
.dropdown-item {
  padding: 0.25rem 1rem;
}
.dropdown-item:hover {
  background-color: #f8f9fa;
}
.search-input {
  border-radius: 0.25rem;
}
/* Style for scrollbar */
.dropdown-options::-webkit-scrollbar {
  width: 8px;
}
.dropdown-options::-webkit-scrollbar-track {
  background: #f1f1f1; 
}
.dropdown-options::-webkit-scrollbar-thumb {
  background: #888; 
  border-radius: 4px;
}
.dropdown-options::-webkit-scrollbar-thumb:hover {
  background: #555; 
}
</style>
            
            <div class="col-md-6 mb-3">
              <label class="form-label">Origin Location</label>
              <select type="text" class="form-select"  name="origin_location" id="originLocation" required>
                  {% for district in districts %}
                  <option value="{{ district }}" {% if candidate.origin_location == district %}selected{% endif %}>
                      {{ district }}
                  </option>
                  {% endfor %}
                  <option value="Other" {% if candidate.origin_location == "Other" %}selected{% endif %}>Other</option>
              </select>
              <div id="otherOriginLocation" style="display: none;" class="mt-2">
          <label class="form-label">Specify Other Origin Location</label>
          <input type="text" class="form-control" name="other_origin_location" 
                 value="{{ candidate.other_origin_location }}" maxlength="100">
          </div>
              <div class="invalid-feedback">
                Maximum 100 characters allowed
              </div>
            </div>
            
            <div class="col-md-6 mb-3">
              <label class="form-label">Qualification</label>
              <select class="form-select" name="qualification" id="qualificationSelect">
                <option value="">Select Qualification</option>
                <option value="High School" {% if candidate.qualification == "High School" %}selected{% endif %}>High School</option>
                <option value="Diploma" {% if candidate.qualification == "Diploma" %}selected{% endif %}>Diploma</option>
                <option value="Bachelor's Degree" {% if candidate.qualification == "Bachelor's Degree" %}selected{% endif %}>Bachelor's Degree</option>
                <option value="Master's Degree" {% if candidate.qualification == "Master's Degree" %}selected{% endif %}>Master's Degree</option>
                <option value="PhD" {% if candidate.qualification == "PhD" %}selected{% endif %}>PhD</option>
                <option value="Other" {% if candidate.qualification == "Other" %}selected{% endif %}>Other</option>
              </select>
              <div id="otherQualificationContainer" style="display: none;" class="mt-2">
                <label class="form-label">Specify Other Qualification</label>
                <input type="text" class="form-control" name="other_qualification" 
                       value="{{ candidate.other_qualification }}" maxlength="100">
              </div>
            </div>
            
            <div class="col-md-6 mb-3">
              <label class="form-label">Diploma</label>
              <input type="text" class="form-control" name="diploma" 
                     value="{{candidate.diploma}}"
                     maxlength="100">
              <div class="invalid-feedback">
                Maximum 100 characters allowed
              </div>
            </div>
            <!-- Bootstrap Multiselect CSS -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-multiselect/1.1.2/css/bootstrap-multiselect.min.css">
           <!-- Sector -->
<!-- Sector -->
<div class="col-sm-6 col-md-6">
    <div class="mb-3">
        <label class="form-label">Sector</label>
        <div class="dropdown">
            <button class="btn btn-outline-secondary dropdown-toggle w-100 text-start" type="button" 
                    id="sectorDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                {% if candidate.sector %}
                    {% if candidate.sector|length > 2 %}
                        {{ candidate.sector|length }} sectors selected
                    {% else %}
                        {{ candidate.sector|join:", " }}
                    {% endif %}
                {% else %}
                    Select sectors...
                {% endif %}
            </button>
            <ul class="dropdown-menu w-100 p-2" aria-labelledby="sectorDropdown">
                <!-- Search Box -->
                <li>
                    <div class="px-2 mb-2">
                        <input type="text" class="form-control sector-search-input" 
                               placeholder="Search sectors..." 
                               id="sectorSearch">
                    </div>
                </li>
                <!-- Options List -->
                <div class="dropdown-options" style="max-height: 250px; overflow-y: auto;">
                    {% for job_sector in job_sectors %}
                    <li class="dropdown-item">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" name="sector" 
                                   value="{{ job_sector }}" id="sector-{{ forloop.counter }}"
                                   {% if job_sector in candidate.sector %}checked{% endif %}>
                            <label class="form-check-label w-100" for="sector-{{ forloop.counter }}">
                                {{ job_sector }}
                            </label>
                        </div>
                    </li>
                    {% endfor %}
                </div>
            </ul>
        </div>
        <div class="invalid-feedback">Please select at least one sector.</div>
    </div>
</div>

<!-- Department -->
<div class="col-sm-6 col-md-6">
    <div class="mb-3">
        <label class="form-label">Department</label>
        <div class="dropdown">
            <button class="btn btn-outline-secondary dropdown-toggle w-100 text-start" type="button" 
                    id="departmentDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                {% if candidate.department %}
                    {% if candidate.department|length > 2 %}
                        {{ candidate.department|length }} departments selected
                    {% else %}
                        {{ candidate.department|join:", " }}
                    {% endif %}
                {% else %}
                    Select departments...
                {% endif %}
            </button>
            <ul class="dropdown-menu w-100 p-2" aria-labelledby="departmentDropdown">
                <!-- Search Box -->
                <li>
                    <div class="px-2 mb-2">
                        <input type="text" class="form-control department-search-input" 
                               placeholder="Search departments..." 
                               id="departmentSearch">
                    </div>
                </li>
                <!-- Options List -->
                <div class="dropdown-options" style="max-height: 250px; overflow-y: auto;">
                    {% for department in departments %}
                    <li class="dropdown-item">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" name="department" 
                                   value="{{ department }}" id="dept-{{ forloop.counter }}"
                                   {% if department in candidate.department %}checked{% endif %}>
                            <label class="form-check-label w-100" for="dept-{{ forloop.counter }}">
                                {{ department }}
                            </label>
                        </div>
                    </li>
                    {% endfor %}
                </div>
            </ul>
        </div>
        <div class="invalid-feedback">Please select at least one department.</div>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    // Initialize both dropdowns
    ['sector', 'department'].forEach(type => {
        const dropdown = document.getElementById(`${type}Dropdown`);
        const checkboxes = document.querySelectorAll(`input[name="${type}"]`);
        const searchInput = document.getElementById(`${type}Search`);
        const dropdownOptions = document.querySelector(`#${type}Dropdown + .dropdown-menu .dropdown-options`);
        
        // Update button text when selections change
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                updateDropdownButtonText(type);
            });
        });
        
        // Search functionality
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                const searchTerm = this.value.toLowerCase();
                const options = dropdownOptions.querySelectorAll('.dropdown-item');
                
                options.forEach(option => {
                    const text = option.textContent.toLowerCase();
                    option.style.display = text.includes(searchTerm) ? 'block' : 'none';
                });
            });
        }
        
        // Initialize button text
        updateDropdownButtonText(type);
    });
    
    // Prevent dropdown from closing when clicking inside
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        menu.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
    
    function updateDropdownButtonText(type) {
        const button = document.getElementById(`${type}Dropdown`);
        const checkboxes = document.querySelectorAll(`input[name="${type}"]:checked`);
        const selectedItems = Array.from(checkboxes).map(cb => cb.nextElementSibling.textContent);
        
        if (selectedItems.length === 0) {
            button.textContent = `Select ${type}s...`;
        } else if (selectedItems.length > 2) {
            button.textContent = `${selectedItems.length} ${type}s selected`;
        } else {
            button.textContent = selectedItems.join(', ');
        }
    }
});
</script>

<style>
.dropdown-item {
    padding: 0.25rem 1rem;
    cursor: pointer;
}
.dropdown-item:hover {
    border : 1px solid #007bff;
}
.search-input {
    border-radius: 0.25rem;
}
.dropdown-options {
    max-height: 250px;
    overflow-y: auto;
}
/* Scrollbar styling */
.dropdown-options::-webkit-scrollbar {
    width: 8px;
}
.dropdown-options::-webkit-scrollbar-track {
    border-radius: 4px;
    border: 1px solid #007bff;
}
.dropdown-options::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 4px;
}
.dropdown-options::-webkit-scrollbar-thumb:hover {
    background: #555;
}
.form-check-label {
    cursor: pointer;
    width: 100%;
}
</style>
            
            <div class="col-md-6 mb-3">
              <label class="form-label">Experience (Years)</label>
              <input type="number" class="form-control" name="experience_year" 
                     value="{{candidate.experience_year}}"
                     min="0" max="50">
              <div class="invalid-feedback">
                Please enter valid years (0-50)
              </div>
            </div>
            
            <div class="col-md-6 mb-3">
              <label class="form-label">Experience (Months)</label>
              <input type="number" class="form-control" name="experience_month" 
                     value="{{candidate.experience_month}}"
                     min="0" max="11">
              <div class="invalid-feedback">
                Please enter valid months (0-11)
              </div>
            </div>
            
            <div class="col-md-6 mb-3">
              <label class="form-label">Current Company</label>
              <input type="text" class="form-control" name="current_company" 
                     value="{{candidate.current_company}}"
                     maxlength="100">
              <div class="invalid-feedback">
                Maximum 100 characters allowed
              </div>
            </div>
            
            <div class="col-md-6 mb-3">
              <label class="form-label">Working Status</label>
              <select class="form-select" name="current_working_status" id="workingStatusSelect">
                <option value="">Select Status</option>
                <option value="Employed" {% if candidate.current_working_status == "Employed" %}selected{% endif %}>Employed</option>
                <option value="Unemployed" {% if candidate.current_working_status == "Unemployed" %}selected{% endif %}>Unemployed</option>
                <option value="Student" {% if candidate.current_working_status == "Student" %}selected{% endif %}>Student</option>
                <option value="Freelancer" {% if candidate.current_working_status == "Freelancer" %}selected{% endif %}>Freelancer</option>
                <option value="Other" {% if candidate.current_working_status == "Other" %}selected{% endif %}>Other</option>
              </select>
              <div id="otherWorkingStatusContainer" style="display: none;" class="mt-2">
                <label class="form-label">Specify Other Working Status</label>
                <input type="text" class="form-control" name="other_working_status" 
                       value="{{ candidate.other_working_status }}" maxlength="100">
              </div>
            </div>
            
            <div class="col-md-6 mb-3">
  <label class="form-label">Current Salary (₹)</label>
  <div class="input-group">
    <input type="number" class="form-control" name="current_salary"
           value="{{ candidate.current_salary }}" min="0" step="1">
    <select class="form-select" name="current_salary_type">
      <option value="(CTC)" {% if candidate.current_salary_type == '(CTC)' %}selected{% endif %}>CTC</option>
      <option value="(Per Month)" {% if candidate.current_salary_type == '(Per Month)' %}selected{% endif %}>Per Month</option>
    </select>
  </div>
  <div class="invalid-feedback">
    Please enter a valid salary
  </div>
</div>

<div class="col-md-6 mb-3">
  <label class="form-label">Expected Salary (₹)</label>
  <div class="input-group">
    <input type="number" class="form-control" name="expected_salary"
           value="{{ candidate.expected_salary }}" min="0" step="1">
    <select class="form-select" name="expected_salary_type">
      <option value="(CTC)" {% if candidate.expected_salary_type == '(CTC)' %}selected{% endif %}>CTC</option>
      <option value="(Per Month)" {% if candidate.expected_salary_type == '(Per Month)' %}selected{% endif %}>Per Month</option>
    </select>
  </div>
  <div class="invalid-feedback">
    Please enter a valid salary
  </div>
</div>

          </div>
          
          <!-- Calling Remark Section -->
          <hr class="my-4">
          <h5 class="text-secondary mb-4">Calling Remark</h5>
          

    <div class="row">
      <!-- Call Connection Status -->
      <div class="col-md-6 mb-3">
        <label class="form-label">Call Connection Status <span class="text-danger">*</span></label>
        <select class="form-select" name="call_connection" id="callConnection" required>
          <option value="" disabled selected>Select Status</option>
          <option value="Connected" {% if candidate.call_connection == "Connected" %}selected{% endif %}>Connected</option>
          <option value="Not Reachable" {% if candidate.call_connection == "Not Reachable" %}selected{% endif %}>Not Reachable</option>
          <option value="Busy" {% if candidate.call_connection == "Busy" %}selected{% endif %}>Busy</option>
          <option value="Wrong Number" {% if candidate.call_connection == "Wrong Number" %}selected{% endif %}>Wrong Number</option>
          <option value="Other" {% if candidate.call_connection == "Other" %}selected{% endif %}>Other</option>
        </select>
        <div id="otherCallConnectionContainer" style="display: none;" class="mt-2">
          <label class="form-label">Specify Other Call Connection Status</label>
          <input type="text" class="form-control" name="other_call_connection" 
                 value="{{ candidate.other_call_connection }}" maxlength="100">
        </div>
        <div class="invalid-feedback">Please select call connection status</div>
      </div>
    </div>

    <!-- Other fields (hidden initially) -->
    <div class="row" id="otherFields" style="display: none;">
      

      <!-- Lead Generate Status -->
      <div class="col-md-6 mb-3">
        <label class="form-label">Lead Generate Status <span class="text-danger">*</span></label>
        <select class="form-select" name="lead_generate" id="leadGenerateSelect" required disabled>
          <option value="" disabled selected>Select Status</option>
          <option value="Yes" {% if candidate.lead_generate == "Yes" %}selected{% endif %}>Yes</option>
          <option value="No" {% if candidate.lead_generate == "No" %}selected{% endif %}>No</option>
          <option value="Converted" {% if candidate.lead_generate == "Converted" %}selected{% endif %}>Converted</option>
          <option value="Other" {% if candidate.lead_generate == "Other" %}selected{% endif %}>Other</option>
        </select>
        <div id="otherLeadGenerateContainer" style="display: none;" class="mt-2">
          <label class="form-label">Specify Other Lead Generate Status</label>
          <input type="text" class="form-control" name="other_lead_generate" 
                 value="{{ candidate.other_lead_generate }}" maxlength="100">
        </div>
        <div class="invalid-feedback">Please select lead status</div>
      </div>

      <!-- Interview Status -->
      <div class="col-md-6 mb-3">
        <label class="form-label">Interview Status <span class="text-danger">*</span></label>
        <select class="form-select" name="send_for_interview" id="interviewStatusSelect" required disabled>
          <option value="" disabled selected>Select Status</option>
          <option value="Yes" {% if candidate.send_for_interview == "Yes" %}selected{% endif %}>Yes</option>
          <option value="No" {% if candidate.send_for_interview == "No" %}selected{% endif %}>No</option>
          <option value="Scheduled" {% if candidate.send_for_interview == "Scheduled" %}selected{% endif %}>Scheduled</option>
          <option value="Not Interested" {% if candidate.send_for_interview == "Not Interested" %}selected{% endif %}>Not Interested</option>
          <option value="Rescheduled" {% if candidate.send_for_interview == "Rescheduled" %}selected{% endif %}>Rescheduled</option>
          <option value="Completed" {% if candidate.send_for_interview == "Completed" %}selected{% endif %}>Completed</option>
          <option value="Other" {% if candidate.send_for_interview == "Other" %}selected{% endif %}>Other</option>
        </select>
        <div id="otherInterviewStatusContainer" style="display: none;" class="mt-2">
          <label class="form-label">Specify Other Interview Status</label>
          <input type="text" class="form-control" name="other_interview_status" 
                 value="{{ candidate.other_interview_status }}" maxlength="100">
        </div>
        <div class="invalid-feedback">Please select interview status</div>
      </div>

      <!-- Next Follow-Up Date -->
      <div class="col-md-6 mb-3">
        <label class="form-label">Next Follow-Up Date <span class="text-danger">*</span></label>
        <input type="date" class="form-control" name="next_follow_up_date" value="{{ candidate.next_follow_up_date|date:'Y-m-d' }}" min="{{ today|date:'Y-m-d' }}" required disabled>
        <div class="invalid-feedback">Please select a valid future date</div>
      </div>

      <!-- Calling Remark -->
      <div class="col-md-6 mb-3">
        <label class="form-label">Calling Remark <span class="text-danger">*</span></label>
        <textarea class="form-control" name="calling_remark" maxlength="500" required disabled>{{ candidate.calling_remark }}</textarea>
        <div class="invalid-feedback">Please enter a remark (max 500 characters)</div>
      </div>
    </div>
          
          <!-- Selection Record Section -->
          <hr class="my-4">
          <h5 class="text-secondary mb-4">Selection Record</h5>
          <!-- Selection Status Dropdown -->
<!-- Selection Status -->
<div class="row">
  <div class="col-md-6 mb-3">
    <label class="form-label">Selection Status</label>
    <select class="form-select" name="selection_status" id="selectionStatus">
      <option value="" disabled selected>Select Status</option>
      <option value="Selected" {% if candidate.selection_status == "Selected" %}selected{% endif %}>Selected</option>
      <option value="Rejected" {% if candidate.selection_status == "Rejected" %}selected{% endif %}>Rejected</option>
      <option value="Pending" {% if candidate.selection_status == "Pending" %}selected{% endif %}>Pending</option>
      <option value="Not Join" {% if candidate.selection_status == "Not Join" %}selected{% endif %}>Not Join</option>
      <option value="Other" {% if candidate.selection_status == "Other" %}selected{% endif %}>Other</option>
    </select>

    <div id="otherSelectionStatusContainer" class="mt-2" style="display: none;">
      <label class="form-label">Specify Other Selection Status</label>
      <input type="text" class="form-control" name="other_selection_status" value="{{ candidate.other_selection_status }}" maxlength="100">
    </div>
  </div>
</div>

<!-- Fields shown when Selection = Selected -->
<div class="row" id="selectionFields" style="display: none;">
  <div class="col-md-6 mb-3">
  <label class="form-label">Company & Job Profile</label>
  <select class="form-select" name="company_name">
    {% for v in vacancies %}
      <option value="{{ v.company__company_name }}"
        {% if candidate.company_name == v.company__company_name %}selected{% endif %}>
        {{ v.job_profile }} - {{ v.company__company_name }}
      </option>
    {% endfor %}
    <option value="Other" {% if candidate.company_name == "Other" %}selected{% endif %}>Other</option>
  </select>
</div>


  <div class="col-md-6 mb-3">
    <label class="form-label">Offered Salary (₹)</label>
    <input type="number" name="offered_salary" class="form-control" value="{{ candidate.offered_salary }}" min="0" step="1">
  </div>

  <div class="col-md-6 mb-3">
    <label class="form-label">Selection Date</label>
    <input type="date" name="selection_date" class="form-control" value="{{ candidate.selection_date|date:'Y-m-d' }}">
  </div>

  <div class="col-md-6 mb-3">
    <label class="form-label">Joining Status</label>
    <select class="form-select" name="joining_status" id="joiningStatus">
      <option value="" disabled selected>Select Joining Status</option>
      <option value="Joined" {% if candidate.joining_status == "Joined" %}selected{% endif %}>Joined</option>
      <option value="Not Joined" {% if candidate.joining_status == "Not Joined" %}selected{% endif %}>Not Joined</option>
    </select>
  </div>
</div>

<!-- Fields shown when Joining Status = Joined -->
<div class="row" id="joinedFields" style="display: none;">
  <div class="col-md-6 mb-3">
    <label class="form-label">Joining Date</label>
    <input type="date" name="candidate_joining_date" class="form-control" value="{{ candidate.candidate_joining_date|date:'Y-m-d' }}">
  </div>

  <div class="col-md-6 mb-3">
    <label class="form-label">Our Commission (₹)</label>
    <input type="number" name="emta_commission" class="form-control" value="{{ candidate.emta_commission }}" min="0" step="1">
  </div>

  <div class="col-md-6 mb-3">
    <label class="form-label">Payout Date</label>
    <input type="date" name="payout_date" class="form-control" value="{{ candidate.payout_date|date:'Y-m-d' }}">
  </div>
</div>


<script>
document.addEventListener("DOMContentLoaded", function () {
  const selectionStatus = document.getElementById("selectionStatus");
  const joiningStatus = document.getElementById("joiningStatus");
  const otherStatusInput = document.getElementById("otherSelectionStatusContainer");
  const selectionFields = document.getElementById("selectionFields");
  const joinedFields = document.getElementById("joinedFields");

  function updateUI() {
    const selection = selectionStatus.value;
    const joining = joiningStatus ? joiningStatus.value : "";

    // Show 'Other' status input
    otherStatusInput.style.display = selection === "Other" ? "block" : "none";

    // Show selection-level fields
    if (selection === "Selected") {
      selectionFields.style.display = "flex";
    } else {
      selectionFields.style.display = "none";
      joinedFields.style.display = "none";
    }

    // Show joined-level fields
    if (selection === "Selected" && joining === "Joined") {
      joinedFields.style.display = "flex";
    } else {
      joinedFields.style.display = "none";
    }
  }

  // Event listeners
  selectionStatus.addEventListener("change", updateUI);
  if (joiningStatus) {
    joiningStatus.addEventListener("change", updateUI);
  }

  // Initial call on load
  updateUI();
});
</script>




        </form>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
        <button type="submit" form="candidateForm" class="btn btn-primary">Save All Changes</button>
      </div>
    </div>
  </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('candidateForm');
  
  // Initialize conditional fields
  const callConnection = document.getElementById('callConnection');
  const otherFieldsWrapper = document.getElementById('otherFields');
  const otherFieldsInputs = otherFieldsWrapper.querySelectorAll('select, textarea, input');
  
  const selectionStatus = document.getElementById('selectionStatus');
  const otherSelectionFieldsWrapper = document.getElementById('otherSelectionFields');
  const otherSelectionFieldsInputs = otherSelectionFieldsWrapper.querySelectorAll('select, input');

  // Function to toggle calling remark fields
  function toggleOtherFields() {
    const isConnected = callConnection.value === 'Connected';
    otherFieldsWrapper.style.display = isConnected ? 'flex' : 'none';
    otherFieldsInputs.forEach(el => {
      el.disabled = !isConnected;
      if (!isConnected) {
        el.required = false;
      } else {
        if (el.name === 'calling_remark' || el.name === 'lead_generate' || 
            el.name === 'send_for_interview' || el.name === 'next_follow_up_date') {
          el.required = true;
        }
      }
    });
  }

  // Function to toggle selection fields
  function toggleSelectionOtherFields() {
    const isSelected = selectionStatus.value === 'Selected';
    otherSelectionFieldsWrapper.style.display = isSelected ? 'flex' : 'none';
    otherSelectionFieldsInputs.forEach(el => {
      el.disabled = !isSelected;
      if (isSelected) {
        if (el.name === 'company_name' || el.name === 'offered_salary' || 
            el.name === 'selection_date') {
          el.required = true;
        }
      } else {
        el.required = false;
      }
    });
  }

  // Function to toggle "Other" input fields
  function toggleOtherInputFields(selectElement, containerId) {
    const container = document.getElementById(containerId);
    if (selectElement.value === 'Other') {
      container.style.display = 'block';
      container.querySelector('input').required = true;
    } else {
      container.style.display = 'none';
      container.querySelector('input').required = false;
    }
  }

  // Initialize all "Other" fields
  function initializeOtherFields() {
    // Lead Source
    toggleOtherInputFields(document.getElementById('leadSourceSelect'), 'otherLeadSourceContainer');
    
    // Qualification
    toggleOtherInputFields(document.getElementById('qualificationSelect'), 'otherQualificationContainer');
    
    // Working Status
    toggleOtherInputFields(document.getElementById('workingStatusSelect'), 'otherWorkingStatusContainer');
    
    // Call Connection
    toggleOtherInputFields(document.getElementById('callConnection'), 'otherCallConnectionContainer');

    // Origin Location
    toggleOtherInputFields(document.getElementById('originLocation'), 'otherOriginLocation');

    // Lead Generate
    toggleOtherInputFields(document.getElementById('leadGenerateSelect'), 'otherLeadGenerateContainer');
    
    // Interview Status
    toggleOtherInputFields(document.getElementById('interviewStatusSelect'), 'otherInterviewStatusContainer');
    
    // Selection Status
    toggleOtherInputFields(document.getElementById('selectionStatus'), 'otherSelectionStatusContainer');
  }

  // Initialize on load
  toggleOtherFields();
  toggleSelectionOtherFields();
  initializeOtherFields();

  // Add change listeners for "Other" fields
  document.getElementById('leadSourceSelect').addEventListener('change', function() {
    toggleOtherInputFields(this, 'otherLeadSourceContainer');
  });
  
  document.getElementById('qualificationSelect').addEventListener('change', function() {
    toggleOtherInputFields(this, 'otherQualificationContainer');
  });
  
  document.getElementById('workingStatusSelect').addEventListener('change', function() {
    toggleOtherInputFields(this, 'otherWorkingStatusContainer');
  });
  
  document.getElementById('callConnection').addEventListener('change', function() {
    toggleOtherInputFields(this, 'otherCallConnectionContainer');
    toggleOtherFields();
  });
  
document.getElementById('originLocation').addEventListener('change', function() {
    toggleOtherInputFields(this, 'otherOriginLocation');
    toggleOtherFields();
  });

  document.getElementById('leadGenerateSelect').addEventListener('change', function() {
    toggleOtherInputFields(this, 'otherLeadGenerateContainer');
  });
  
  document.getElementById('interviewStatusSelect').addEventListener('change', function() {
    toggleOtherInputFields(this, 'otherInterviewStatusContainer');
  });
  
  document.getElementById('selectionStatus').addEventListener('change', function() {
    toggleOtherInputFields(this, 'otherSelectionStatusContainer');
    toggleSelectionOtherFields();
  });

  // Form submission validation
  form.addEventListener('submit', function(event) {
    event.preventDefault();
    
    // Reset custom validity
    const allInputs = form.querySelectorAll('input, select, textarea');
    allInputs.forEach(input => input.setCustomValidity(''));
    
    // Check form validity
    if (!form.checkValidity()) {
      event.stopPropagation();
      form.classList.add('was-validated');
      
      // Manually check conditional required fields
      if (callConnection.value === 'Connected') {
        otherFieldsInputs.forEach(el => {
          if (el.required && !el.value) {
            el.classList.add('is-invalid');
          }
        });
      }
      
      if (selectionStatus.value === 'Selected') {
        otherSelectionFieldsInputs.forEach(el => {
          if (el.required && !el.value) {
            el.classList.add('is-invalid');
          }
        });
      }
      
      // Check "Other" fields if they're visible
      document.querySelectorAll('[id$="Container"]').forEach(container => {
        if (container.style.display !== 'none' && !container.querySelector('input').value) {
          container.querySelector('input').classList.add('is-invalid');
        }
      });
      
      return;
    }
    
    // Validate file sizes
    if (!validateFileSize('candidate_photo', 10) || !validateFileSize('candidate_resume', 10)) {
      return;
    }
    
    // Validate expected salary is >= current salary if both exist
    const currentSalary = parseFloat(form.querySelector('input[name="current_salary"]').value) || 0;
    const expectedSalary = parseFloat(form.querySelector('input[name="expected_salary"]').value) || 0;
    
    if (expectedSalary > 0 && expectedSalary < currentSalary) {
      const expectedSalaryInput = form.querySelector('input[name="expected_salary"]');
      expectedSalaryInput.setCustomValidity('Expected salary should be ≥ current salary');
      expectedSalaryInput.classList.add('is-invalid');
      form.classList.add('was-validated');
      return;
    }
    
    // Submit form via AJAX
    submitForm();
  });
  
  function validateFileSize(fieldName, maxSizeMB) {
    const fileInput = form.querySelector(`input[name="${fieldName}"]`);
    if (fileInput.files.length > 0) {
      const fileSize = fileInput.files[0].size / 1024 / 1024; // in MB
      if (fileSize > maxSizeMB) {
        fileInput.setCustomValidity(`File size should not exceed ${maxSizeMB}MB`);
        fileInput.classList.add('is-invalid');
        form.classList.add('was-validated');
        return false;
      }
    }
    return true;
  }
  
  function submitForm() {
    const formData = new FormData(form);
    const submitBtn = document.querySelector('button[type="submit"][form="candidateForm"]');
    const originalBtnText = submitBtn.innerHTML;
    
    // Show loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
    
    fetch(form.action, {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value
      }
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      if (data.success) {
        showAlert('success', data.message);
        
        // If this is a new candidate, redirect or refresh as needed
        if (window.location.pathname.includes('add')) {
          setTimeout(() => {
            window.location.href = data.redirect_url || window.location.href;
          }, 1500);
        } else {
          // For edit, just close the modal after delay
          setTimeout(() => {
            const modal = bootstrap.Modal.getInstance(document.getElementById('modal-candidate'));
            if (modal) modal.hide();
          }, 1500);
        }
      } else {
        showAlert('danger', data.message || 'Error saving data');
        
        // Show field errors if any
        if (data.errors) {
          Object.entries(data.errors).forEach(([field, error]) => {
            const input = form.querySelector(`[name="${field}"]`);
            if (input) {
              input.setCustomValidity(error);
              input.classList.add('is-invalid');
            }
          });
          form.classList.add('was-validated');
        }
      }
    })
    .catch(error => {
      console.error('Error:', error);
      showAlert('danger', 'Error saving data. Please try again.');
    })
    .finally(() => {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalBtnText;
    });
  }
  
  function showAlert(type, message) {
    // Remove any existing alerts
    const existingAlert = form.querySelector('.alert');
    if (existingAlert) {
      existingAlert.remove();
    }
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    form.prepend(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      alertDiv.classList.remove('show');
      setTimeout(() => alertDiv.remove(), 150);
    }, 5000);
  }
  
  // Real-time validation
  const inputs = form.querySelectorAll('input, select, textarea');
  inputs.forEach(input => {
    input.addEventListener('input', () => {
      if (input.checkValidity()) {
        input.classList.remove('is-invalid');
      } else {
        input.classList.add('is-invalid');
      }
      
      // Special handling for expected salary
      if (input.name === 'expected_salary') {
        const currentSalary = parseFloat(form.querySelector('input[name="current_salary"]').value) || 0;
        const expectedSalary = parseFloat(input.value) || 0;
        
        if (expectedSalary > 0 && expectedSalary < currentSalary) {
          input.setCustomValidity('Expected salary should be ≥ current salary');
          input.classList.add('is-invalid');
        } else {
          input.setCustomValidity('');
        }
      }
    });
    
    input.addEventListener('blur', () => {
      if (!input.checkValidity()) {
        input.classList.add('is-invalid');
      }
    });
  });
});
</script>