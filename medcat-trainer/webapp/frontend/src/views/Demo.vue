<template>
  <div class="container-fluid demo">
    <div class="demo-text">
      <form @submit.prevent>
        <div class="form-group">
          <label>Project Model:</label>
          <select class="form-control" v-model="selectedProject">
            <option :value="proj" v-for="proj of projects" :key="proj.id">{{proj.name}}
            </option>
          </select>
        </div>

        <!-- Sample Letters Dropdown -->
        <div class="form-group">
          <label>Quick Load Sample Letter:</label>
          <select class="form-control" v-model="selectedSample" @change="loadSampleLetter">
            <option :value="null">-- Select a sample letter --</option>
            <option :value="sample" v-for="(sample, index) of sampleLetters" :key="index">
              {{ sample.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>Text to Annotate:</label>
          <textarea v-model="exampleText" class="form-control" name="text" rows="10"
                    placeholder="Paste clinical text here or select a sample letter above..."></textarea>
        </div>
        <div class="form-group">
          <label>CUI Filter</label>
          <textarea v-model="cuiFilters" class="form-control" name="cui"
                    rows="3" placeholder="Comma separated list: S-91175000, S-84757009"></textarea>
        </div>
        <button @click="annotate()" class="btn btn-primary btn-lg btn-block"
                :disabled="!selectedProject.id || !exampleText">
          <span v-if="loadingMsg">{{ loadingMsg }}</span>
          <span v-else>Annotate Text</span>
        </button>
      </form>

      <!-- Regex Extractions Panel -->
      <div class="regex-extractions" v-if="regexExtractions && hasRegexResults">
        <h5>Clinical Letter Fields (Regex Extracted)</h5>
        <table class="table table-sm table-bordered">
          <tbody>
            <tr v-if="regexExtractions.nhs_number">
              <th>NHS Number</th>
              <td><span class="badge badge-info">{{ regexExtractions.nhs_number }}</span></td>
            </tr>
            <tr v-if="regexExtractions.consultant">
              <th>Consultant</th>
              <td><span class="badge badge-success">{{ regexExtractions.consultant }}</span></td>
            </tr>
            <tr v-if="regexExtractions.specialty">
              <th>Specialty</th>
              <td><span class="badge badge-warning">{{ regexExtractions.specialty }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Stats Panel -->
      <div class="stats-panel" v-if="ents.length > 0">
        <h5>Annotation Statistics</h5>
        <div class="stat-item">
          <span class="stat-label">MedCAT Entities:</span>
          <span class="stat-value">{{ medcatEntityCount }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Regex Extractions:</span>
          <span class="stat-value regex">{{ regexEntityCount }}</span>
        </div>
        <div class="stat-item total">
          <span class="stat-label">Total Highlights:</span>
          <span class="stat-value">{{ ents.length }}</span>
        </div>
      </div>
    </div>
    <div class="view-port">
      <div class="clinical-text">
        <clinical-text :loading="loadingMsg" :text="annotatedText" :ents="ents"
                       :taskName="task" :taskValues="taskValues" @select:concept="selectEntity"></clinical-text>
      </div>
      <div class="sidebar">
        <concept-summary :selectedEnt="currentEnt" :project="selectedProject"
                         :searchFilterDBIndex="searchFilterDBIndex"></concept-summary>
      </div>
    </div>
  </div>
</template>

<script>
import ClinicalText from '@/components/common/ClinicalText.vue'
import ConceptSummary from '@/components/common/ConceptSummary.vue'

const TASK_NAME = 'Concept Anno'
const VALUES = ['Val']

// Sample clinical letters for quick demonstration
const SAMPLE_LETTERS = [
  {
    name: 'Cardiology - Chest Pain',
    text: `NHS Number: 123 456 7890
Consultant: Dr. Sarah Johnson
Specialty: Cardiology

Dear Dr. Smith,

Re: Mr. John Davies, DOB: 15/03/1958

Thank you for referring this 65-year-old gentleman who presented with chest pain and shortness of breath on exertion.

History of Presenting Complaint:
The patient reports a 3-month history of central chest discomfort, described as a "tight" sensation, occurring on moderate exertion. The pain typically resolves within 5 minutes of rest.

Past Medical History:
- Type 2 Diabetes Mellitus (diagnosed 2015)
- Hypertension (on treatment)
- Hypercholesterolaemia
- Family history of coronary artery disease

Current Medications:
- Metformin 1g BD
- Ramipril 5mg OD
- Atorvastatin 40mg ON
- Aspirin 75mg OD

Examination:
BP: 142/88 mmHg, HR: 78 bpm regular, BMI: 29
Heart sounds: Normal S1 S2, no murmurs

Assessment:
This gentleman presents with typical stable angina symptoms.

Plan:
1. Exercise tolerance test arranged
2. Commence GTN spray PRN
3. Review in 6 weeks

Dr. Sarah Johnson
Consultant Cardiologist`
  },
  {
    name: 'Respiratory - COPD',
    text: `NHS Number: 987 654 3210
Consultant: Dr. Michael Chen
Specialty: Respiratory Medicine

Dear Dr. Williams,

Re: Mrs. Margaret Thompson, DOB: 22/08/1945

I reviewed this 78-year-old lady regarding her chronic cough and progressive breathlessness.

History:
Mrs. Thompson reports worsening breathlessness over 18 months, now limiting her to walking 100 metres. She has a persistent productive cough with white sputum.

Smoking History: 40 pack-year history, stopped 5 years ago.

Past Medical History:
- COPD (GOLD Stage III)
- Osteoporosis
- Atrial fibrillation
- Previous pulmonary embolism (2019)

Current Medications:
- Seretide 500 Accuhaler BD
- Tiotropium 18mcg OD
- Salbutamol PRN
- Rivaroxaban 20mg OD

Spirometry:
FEV1: 0.92L (42% predicted)
FVC: 2.1L (78% predicted)

Assessment:
Severe COPD with progressive symptoms.

Plan:
1. Pulmonary rehabilitation referral
2. Add Roflumilast 500mcg OD
3. Home oxygen assessment

Dr. Michael Chen
Consultant Respiratory Physician`
  },
  {
    name: 'Neurology - Migraine',
    text: `NHS Number: 456 789 0123
Consultant: Dr. Emma Wilson
Specialty: Neurology

Dear Dr. Brown,

Re: Ms. Rebecca Foster, DOB: 10/11/1982

This 41-year-old teacher presents with recurring headaches and visual disturbance.

History:
Ms. Foster describes 6-month history of severe, unilateral throbbing headaches affecting the right temple. Episodes last 4-72 hours with nausea, photophobia, and phonophobia. Visual aura precedes 50% of attacks.

Past Medical History:
- Migraine with aura (since age 25)
- Depression (stable on sertraline)

Current Medications:
- Sertraline 50mg OD
- Sumatriptan 50mg PRN

Examination:
Neurological examination: Normal
BP: 118/72 mmHg

Assessment:
Chronic migraine with aura, poorly controlled.

Plan:
1. Start Topiramate 25mg ON for prophylaxis
2. Headache diary provided
3. MRI brain arranged
4. Review in 8 weeks

Dr. Emma Wilson
Consultant Neurologist`
  },
  {
    name: 'Diabetes - Annual Review',
    text: `NHS Number: 321 654 9870
Consultant: Dr. Raj Patel
Specialty: Endocrinology/Diabetes

Dear Dr. Taylor,

Re: Mr. Ahmed Khan, DOB: 03/06/1970

Annual review for insulin optimisation.

History:
53-year-old gentleman with Type 2 Diabetes diagnosed 12 years ago. On insulin for 3 years. Variable blood glucose: fasting 8-12 mmol/L, post-prandial 15-18 mmol/L.

Past Medical History:
- Type 2 Diabetes Mellitus
- Diabetic retinopathy (background)
- Microalbuminuria
- Hypertension
- Obesity (BMI 34)

Current Medications:
- Lantus 42 units ON
- Metformin 1g BD
- Linagliptin 5mg OD
- Ramipril 10mg OD

Results:
- HbA1c: 8.4% (target <7%)
- eGFR: 62 (stage 3a CKD)

Assessment:
Suboptimal glycaemic control despite basal insulin.

Plan:
1. Increase Lantus to 48 units ON
2. Add Empagliflozin 10mg OD
3. Dietitian referral
4. Review in 3 months

Dr. Raj Patel
Consultant Diabetologist`
  },
  {
    name: 'Gastroenterology - Colonoscopy',
    text: `NHS Number: 789 012 3456
Consultant: Dr. Lisa Murphy
Specialty: Gastroenterology

Dear Dr. Anderson,

Re: Mrs. Susan Clark, DOB: 28/02/1965

Regarding ongoing GI symptoms and recent colonoscopy findings.

History:
58-year-old lady with 4-month history of altered bowel habit, loose stools 3-4 times daily, crampy abdominal pain, and occasional rectal bleeding.

Past Medical History:
- Irritable bowel syndrome (diagnosed 2010)
- Appendicectomy (1985)

Investigations:
Colonoscopy: Two sessile polyps in sigmoid colon (8mm and 5mm), removed by snare polypectomy. Histology awaited.

Bloods:
- Hb 118 (mild anaemia), MCV 76
- Ferritin: 12 (low)
- Coeliac serology: Negative

Assessment:
Sigmoid polyps with iron deficiency anaemia.

Plan:
1. Await histology
2. Start Ferrous Fumarate 210mg TDS
3. OGD arranged
4. Repeat FBC in 6 weeks

Dr. Lisa Murphy
Consultant Gastroenterologist`
  }
]

export default {
  name: 'Demo',
  components: {
    ClinicalText,
    ConceptSummary
  },
  data () {
    return {
      exampleText: '',
      projects: [],
      selectedProject: {},
      selectedSample: null,
      sampleLetters: SAMPLE_LETTERS,
      cuiFilters: '',
      ents: [],
      currentEnt: {},
      annotatedText: '',
      loadingMsg: null,
      task: TASK_NAME,
      taskValues: VALUES,
      searchFilterDBIndex: null,
      regexExtractions: null
    }
  },
  computed: {
    hasRegexResults () {
      return this.regexExtractions && (
        this.regexExtractions.nhs_number ||
        this.regexExtractions.consultant ||
        this.regexExtractions.specialty
      )
    },
    medcatEntityCount () {
      return this.ents.filter(e => !e.isRegex).length
    },
    regexEntityCount () {
      return this.ents.filter(e => e.isRegex).length
    }
  },
  created () {
    let projectList = []
    let that = this
    const baseUrl = '/api/project-annotate-entities/'
    let getProjects = function (url) {
      that.$http.get(url).then(resp => {
        if (resp.data.count === (projectList.length + resp.data.results.length)) {
          that.projects = projectList.concat(resp.data.results)
          // Auto-select Demo Project if it exists
          that.autoSelectDemoProject()
        } else {
          const nextUrl = `${baseUrl}?${resp.data.next.split('?').slice(-1)}`
          projectList = projectList.concat(resp.data.results)
          getProjects(nextUrl)
        }
      })
    }
    getProjects(baseUrl)
  },
  methods: {
    autoSelectDemoProject () {
      // Try to find and auto-select the Demo Project
      const demoProject = this.projects.find(p => p.name === 'Demo Project')
      if (demoProject) {
        this.selectedProject = demoProject
      } else if (this.projects.length > 0) {
        // Fall back to first available project
        this.selectedProject = this.projects[0]
      }
    },
    loadSampleLetter () {
      if (this.selectedSample) {
        this.exampleText = this.selectedSample.text
        // Clear previous results
        this.ents = []
        this.annotatedText = ''
        this.regexExtractions = null
        this.currentEnt = {}
      }
    },
    annotate () {
      if (!this.selectedProject.id) {
        alert('Please select a project first')
        return
      }
      if (!this.exampleText) {
        alert('Please enter or select text to annotate')
        return
      }
      const payload = {
        project_id: this.selectedProject.id,
        message: this.exampleText,
        cuis: this.cuiFilters,
      }
      this.loadingMsg = 'Annotating Text...'
      this.$http.post('/api/annotate-text/', payload).then(resp => {
        this.loadingMsg = null

        // Process MedCAT entities
        let allEnts = resp.data['entities'].map(e => {
          e.assignedValues = {}
          e.assignedValues[this.task] = this.taskValues[0]
          e.isRegex = false
          return e
        })

        // Capture regex extractions
        this.regexExtractions = resp.data['regex_extractions'] || null

        // Add regex highlights as entities for display
        if (this.regexExtractions && this.regexExtractions.highlights) {
          const regexEnts = this.regexExtractions.highlights.map((h, idx) => ({
            entity: `regex_${h.type}_${idx}`,
            value: h.value,
            start_ind: h.start,
            end_ind: h.end,
            acc: 1.0,
            cui: h.type,
            pretty_name: h.label,
            isRegex: true,
            regexType: h.type,
            assignedValues: { [this.task]: 'Regex' }
          }))
          allEnts = allEnts.concat(regexEnts)
        }

        // Sort all entities by start position
        allEnts.sort((a, b) => a.start_ind - b.start_ind)

        this.ents = allEnts
        this.currentEnt = this.ents.length > 0 ? this.ents[0] : null
        this.annotatedText = resp.data['message']
      }).catch(err => {
        this.loadingMsg = null
        console.error('Annotation error:', err)
        alert('Error annotating text. Please check the console for details.')
      })
    },
    selectEntity (entIndex) {
      this.currentEnt = this.ents[entIndex]
    },
    fetchCDBSearchIndex () {
      if (this.selectedProject.cdb_search_filter && this.selectedProject.cdb_search_filter.length > 0) {
        this.$http.get(`/api/concept-dbs/${this.selectedProject.cdb_search_filter[0]}/`).then(resp => {
          if (resp.data) {
            this.searchFilterDBIndex = `${resp.data.name}_id_${this.selectedProject.cdb_search_filter}`
          }
        })
      }
    }
  },
  watch: {
    'selectedProject': {
      handler () {
        this.fetchCDBSearchIndex()
      }
    }
  }
}
</script>

<style scoped lang="scss">
.demo {
  height: calc(100% - 71px);
  display: flex;
}

.demo-text {
  flex-direction: column;
  flex: 0 0 420px;
  height: 100%;
  overflow-y: auto;
  background-color: #f8f9fa;
  border-right: 1px solid #dee2e6;
}

.view-port {
  flex: 1 1 auto;
  display: flex;
}

.clinical-text {
  height:100%;
  flex-direction: column;
  flex: 1 1 auto;
}

.sidebar {
  height:100%;
  flex-direction: column;
  flex: 0 0 350px;
}

form {
  margin: 15px;
  padding: 15px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.form-group {
  margin-bottom: 15px;

  label {
    font-weight: 600;
    color: #495057;
    margin-bottom: 5px;
    font-size: 13px;
  }
}

.btn-primary {
  background-color: #007bff;
  border-color: #007bff;
  font-weight: 600;

  &:disabled {
    background-color: #6c757d;
    border-color: #6c757d;
    cursor: not-allowed;
  }
}

.regex-extractions {
  margin: 15px;
  padding: 15px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);

  h5 {
    margin-bottom: 12px;
    color: #495057;
    font-size: 14px;
    font-weight: 600;
    border-bottom: 1px solid #dee2e6;
    padding-bottom: 8px;
  }

  table {
    margin-bottom: 0;
    font-size: 13px;

    th {
      width: 100px;
      background-color: #e9ecef;
      font-weight: 500;
    }

    td {
      .badge {
        font-size: 12px;
        font-weight: 500;
        padding: 5px 10px;
      }

      .badge-info {
        background-color: #17a2b8;
      }

      .badge-success {
        background-color: #28a745;
      }

      .badge-warning {
        background-color: #ffc107;
        color: #212529;
      }
    }
  }
}

.stats-panel {
  margin: 15px;
  padding: 15px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);

  h5 {
    margin-bottom: 12px;
    color: #495057;
    font-size: 14px;
    font-weight: 600;
    border-bottom: 1px solid #dee2e6;
    padding-bottom: 8px;
  }

  .stat-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 5px 0;

    .stat-label {
      color: #6c757d;
      font-size: 13px;
    }

    .stat-value {
      font-weight: 600;
      color: #28a745;
      font-size: 16px;

      &.regex {
        color: #17a2b8;
      }
    }

    &.total {
      border-top: 1px solid #dee2e6;
      margin-top: 8px;
      padding-top: 8px;

      .stat-label {
        font-weight: 600;
        color: #495057;
      }

      .stat-value {
        color: #007bff;
        font-size: 18px;
      }
    }
  }
}
</style>
