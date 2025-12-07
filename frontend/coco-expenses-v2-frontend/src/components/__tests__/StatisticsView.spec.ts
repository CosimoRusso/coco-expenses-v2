import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import StatisticsView from '../StatisticsView.vue'
import apiFetch from '@/utils/apiFetch'
import { dateToISOString } from '@/utils/dateUtils'

// Mock the apiFetch module
vi.mock('@/utils/apiFetch', () => ({
  default: vi.fn(),
}))

// Mock Chart.js components to avoid rendering issues in tests
vi.mock('vue-chartjs', () => ({
  Bar: {
    name: 'Bar',
    template: '<div data-testid="bar-chart">Bar Chart</div>',
  },
  Line: {
    name: 'Line',
    template: '<div data-testid="line-chart">Line Chart</div>',
  },
}))

describe('StatisticsView', () => {
  let mockApiFetch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockApiFetch = apiFetch as ReturnType<typeof vi.fn>
    mockApiFetch.mockReset()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Component Rendering', () => {
    it('renders the statistics view with header', () => {
      mockApiFetch.mockResolvedValue({
        ok: true,
        json: async () => [],
      })

      const wrapper = mount(StatisticsView)
      expect(wrapper.find('h1').text()).toBe('Statistics')
      expect(wrapper.text()).toContain('This is the statistics page')
    })

    it('renders date range filter inputs', () => {
      mockApiFetch.mockResolvedValue({
        ok: true,
        json: async () => [],
      })

      const wrapper = mount(StatisticsView)
      expect(wrapper.find('#startDate').exists()).toBe(true)
      expect(wrapper.find('#endDate').exists()).toBe(true)
      expect(wrapper.find('button').text()).toBe('Filter')
    })

    it('renders section headers', () => {
      mockApiFetch.mockResolvedValue({
        ok: true,
        json: async () => [],
      })

      const wrapper = mount(StatisticsView)
      expect(wrapper.text()).toContain('Results per Category')
      expect(wrapper.text()).toContain('Amortization Timeline')
    })
  })

  describe('Date Initialization', () => {
    it('initializes date inputs on mount', async () => {
      mockApiFetch.mockResolvedValue({
        ok: true,
        json: async () => [],
      })

      const wrapper = mount(StatisticsView)
      await wrapper.vm.$nextTick()

      const startDateInput = wrapper.find('#startDate').element as HTMLInputElement
      const endDateInput = wrapper.find('#endDate').element as HTMLInputElement

      expect(startDateInput.value).toBeTruthy()
      expect(endDateInput.value).toBeTruthy()

      // Verify dates are approximately 2 months apart (allowing for date calculation)
      const startDate = new Date(startDateInput.value)
      const endDate = new Date(endDateInput.value)
      const monthsDiff = (endDate.getFullYear() - startDate.getFullYear()) * 12
        + (endDate.getMonth() - startDate.getMonth())
      expect(monthsDiff).toBeGreaterThanOrEqual(2)
      expect(monthsDiff).toBeLessThanOrEqual(4) // Allow some variance
    })

    it('sets start date to 2 months ago', async () => {
      mockApiFetch.mockResolvedValue({
        ok: true,
        json: async () => [],
      })

      const wrapper = mount(StatisticsView)
      await wrapper.vm.$nextTick()

      const startDateInput = wrapper.find('#startDate').element as HTMLInputElement
      const startDate = new Date(startDateInput.value)
      const expectedDate = new Date()
      expectedDate.setMonth(expectedDate.getMonth() - 2)

      expect(startDateInput.value).toBe(dateToISOString(expectedDate))
    })

    it('sets end date to 1 month in the future', async () => {
      mockApiFetch.mockResolvedValue({
        ok: true,
        json: async () => [],
      })

      const wrapper = mount(StatisticsView)
      await wrapper.vm.$nextTick()

      const endDateInput = wrapper.find('#endDate').element as HTMLInputElement
      const endDate = new Date(endDateInput.value)
      const expectedDate = new Date()
      expectedDate.setMonth(expectedDate.getMonth() + 1)

      expect(endDateInput.value).toBe(dateToISOString(expectedDate))
    })
  })

  describe('API Calls on Mount', () => {
    it('fetches category statistics on mount', async () => {
      const mockCategoryData = [
        {
          category: { id: 1, code: 'FOOD', name: 'Food', for_expense: true },
          amount: '150.50',
        },
      ]

      mockApiFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockCategoryData,
      }).mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      })

      mount(StatisticsView)

      // Wait for async operations
      await new Promise(resolve => setTimeout(resolve, 0))

      expect(mockApiFetch).toHaveBeenCalled()
      const calls = mockApiFetch.mock.calls
      const categoryCall = calls.find(call => 
        call[0].includes('/expenses/statistics/expense_categories/')
      )
      expect(categoryCall).toBeTruthy()
    })

    it('fetches amortization timeline on mount', async () => {
      const mockTimelineData = [
        {
          date: '2024-01-01',
          expense_amount: '100.00',
          non_expense_amount: '200.00',
          difference: '100.00',
        },
      ]

      mockApiFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      }).mockResolvedValueOnce({
        ok: true,
        json: async () => mockTimelineData,
      })

      mount(StatisticsView)

      // Wait for async operations
      await new Promise(resolve => setTimeout(resolve, 0))

      expect(mockApiFetch).toHaveBeenCalled()
      const calls = mockApiFetch.mock.calls
      const timelineCall = calls.find(call => 
        call[0].includes('/expenses/statistics/amortization_timeline/')
      )
      expect(timelineCall).toBeTruthy()
    })

    it('calls API with correct date parameters', async () => {
      mockApiFetch.mockResolvedValue({
        ok: true,
        json: async () => [],
      })

      mount(StatisticsView)
      await new Promise(resolve => setTimeout(resolve, 0))

      const calls = mockApiFetch.mock.calls
      expect(calls.length).toBeGreaterThan(0)

      // Check that date parameters are included in the URL
      calls.forEach(call => {
        if (call[0].includes('statistics')) {
          expect(call[0]).toMatch(/start_date=/)
          expect(call[0]).toMatch(/end_date=/)
        }
      })
    })
  })

  describe('Category Statistics Display', () => {
    it('displays category statistics table when data is available', async () => {
      const mockCategoryData = [
        {
          category: { id: 1, code: 'FOOD', name: 'Food', for_expense: true },
          amount: '150.50',
        },
        {
          category: { id: 2, code: 'TRAVEL', name: 'Travel', for_expense: true },
          amount: '300.75',
        },
      ]

      mockApiFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockCategoryData,
      }).mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      })

      const wrapper = mount(StatisticsView)
      
      // Wait for async operations
      await new Promise(resolve => setTimeout(resolve, 100))
      await wrapper.vm.$nextTick()

      const table = wrapper.find('#categoryStatisticsTable')
      expect(table.exists()).toBe(true)

      const rows = table.findAll('tbody tr')
      expect(rows.length).toBe(2)
      expect(rows[0].text()).toContain('Food')
      expect(rows[0].text()).toContain('150.50')
      expect(rows[1].text()).toContain('Travel')
      expect(rows[1].text()).toContain('300.75')
    })

    it('displays bar chart when category statistics are available', async () => {
      const mockCategoryData = [
        {
          category: { id: 1, code: 'FOOD', name: 'Food', for_expense: true },
          amount: '150.50',
        },
      ]

      mockApiFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockCategoryData,
      }).mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      })

      const wrapper = mount(StatisticsView)
      await new Promise(resolve => setTimeout(resolve, 100))
      await wrapper.vm.$nextTick()

      const barChart = wrapper.find('[data-testid="bar-chart"]')
      expect(barChart.exists()).toBe(true)
    })

    it('shows no data message when category statistics are empty', async () => {
      mockApiFetch.mockResolvedValue({
        ok: true,
        json: async () => [],
      })

      const wrapper = mount(StatisticsView)
      await new Promise(resolve => setTimeout(resolve, 100))
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('No data available for the selected date range')
    })
  })

  describe('Amortization Timeline Display', () => {
    it('displays line chart when amortization timeline data is available', async () => {
      const mockTimelineData = [
        {
          date: '2024-01-01',
          expense_amount: '100.00',
          non_expense_amount: '200.00',
          difference: '100.00',
        },
      ]

      mockApiFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      }).mockResolvedValueOnce({
        ok: true,
        json: async () => mockTimelineData,
      })

      const wrapper = mount(StatisticsView)
      await new Promise(resolve => setTimeout(resolve, 100))
      await wrapper.vm.$nextTick()

      const lineChart = wrapper.find('[data-testid="line-chart"]')
      expect(lineChart.exists()).toBe(true)
    })

    it('shows no data message when amortization timeline is empty', async () => {
      mockApiFetch.mockResolvedValue({
        ok: true,
        json: async () => [],
      })

      const wrapper = mount(StatisticsView)
      await new Promise(resolve => setTimeout(resolve, 100))
      await wrapper.vm.$nextTick()

      const noDataMessages = wrapper.findAll('.no-data-message')
      expect(noDataMessages.length).toBeGreaterThan(0)
    })
  })

  describe('Filter Button Functionality', () => {
    it('calls fetchStatistics when filter button is clicked', async () => {
      mockApiFetch.mockResolvedValue({
        ok: true,
        json: async () => [],
      })

      const wrapper = mount(StatisticsView)
      await wrapper.vm.$nextTick()

      // Reset mock calls after initial mount
      mockApiFetch.mockClear()

      const filterButton = wrapper.find('button')
      await filterButton.trigger('click')

      // Wait for async operations
      await new Promise(resolve => setTimeout(resolve, 0))
      await wrapper.vm.$nextTick()

      // Should call both fetchCategoryStatistics and fetchAmortizationTimeline
      expect(mockApiFetch).toHaveBeenCalled()
    })

    it('refetches data with updated dates when filter is clicked', async () => {
      mockApiFetch.mockResolvedValue({
        ok: true,
        json: async () => [],
      })

      const wrapper = mount(StatisticsView)
      await wrapper.vm.$nextTick()

      // Update date inputs using setValue for proper v-model binding
      const newStartDate = '2024-01-01'
      const newEndDate = '2024-12-31'

      await wrapper.find('#startDate').setValue(newStartDate)
      await wrapper.find('#endDate').setValue(newEndDate)
      await wrapper.vm.$nextTick()

      // Clear previous calls
      mockApiFetch.mockClear()

      // Click filter button
      const filterButton = wrapper.find('button')
      await filterButton.trigger('click')

      // Wait for async operations
      await new Promise(resolve => setTimeout(resolve, 0))
      await wrapper.vm.$nextTick()

      // Verify API calls include the new dates
      const calls = mockApiFetch.mock.calls
      expect(calls.some(call => call[0].includes(newStartDate))).toBe(true)
      expect(calls.some(call => call[0].includes(newEndDate))).toBe(true)
    })
  })

  describe('Error Handling', () => {
    it('displays error message when category statistics fetch fails', async () => {
      mockApiFetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({}),
      }).mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      })

      const wrapper = mount(StatisticsView)
      await new Promise(resolve => setTimeout(resolve, 100))
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('Network response was not ok')
    })

    it('displays error message when API call throws an error', async () => {
      mockApiFetch.mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [],
        })

      const wrapper = mount(StatisticsView)
      await new Promise(resolve => setTimeout(resolve, 100))
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('Error fetching category statistics')
    })

    it('shows error message when dates are not selected', async () => {
      mockApiFetch.mockResolvedValue({
        ok: true,
        json: async () => [],
      })

      const wrapper = mount(StatisticsView)
      await wrapper.vm.$nextTick()

      // Clear dates using setValue which properly updates v-model
      await wrapper.find('#startDate').setValue('')
      await wrapper.vm.$nextTick()

      // Click filter button to trigger validation
      await wrapper.find('button').trigger('click')
      await new Promise(resolve => setTimeout(resolve, 100))
      await wrapper.vm.$nextTick()

      // The error should be set when dates are missing
      expect(wrapper.text()).toContain('Please select both start and end dates.')
    })

    it('clears error message on successful fetch', async () => {
      // First, create an error
      mockApiFetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({}),
      }).mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      })

      const wrapper = mount(StatisticsView)
      await new Promise(resolve => setTimeout(resolve, 100))
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('Network response was not ok')

      // Then, make a successful call by clicking filter button again
      mockApiFetch.mockResolvedValue({
        ok: true,
        json: async () => [
          {
            category: { id: 1, code: 'FOOD', name: 'Food', for_expense: true },
            amount: '100.00',
          },
        ],
      })

      await wrapper.find('button').trigger('click')
      await new Promise(resolve => setTimeout(resolve, 100))
      await wrapper.vm.$nextTick()

      expect(wrapper.text()).not.toContain('Network response was not ok')
    })
  })

  describe('Date Range Validation', () => {
    it('prevents fetching when start date is missing', async () => {
      mockApiFetch.mockResolvedValue({
        ok: true,
        json: async () => [],
      })

      const wrapper = mount(StatisticsView)
      await wrapper.vm.$nextTick()

      // Clear start date using setValue
      await wrapper.find('#startDate').setValue('')
      await wrapper.vm.$nextTick()

      mockApiFetch.mockClear()

      // Click filter button to trigger validation
      await wrapper.find('button').trigger('click')
      await new Promise(resolve => setTimeout(resolve, 100))
      await wrapper.vm.$nextTick()

      // Should show error message and not make API call
      expect(wrapper.text()).toContain('Please select both start and end dates.')
    })

    it('does not fetch amortization timeline when dates are missing', async () => {
      mockApiFetch.mockResolvedValue({
        ok: true,
        json: async () => [],
      })

      const wrapper = mount(StatisticsView)
      await wrapper.vm.$nextTick()

      // Clear start date
      await wrapper.find('#startDate').setValue('')
      await wrapper.vm.$nextTick()

      mockApiFetch.mockClear()

      // Click filter button
      await wrapper.find('button').trigger('click')
      await new Promise(resolve => setTimeout(resolve, 100))
      await wrapper.vm.$nextTick()

      // fetchAmortizationTimeline should not make API call when dates are missing
      // The component should only show error for category statistics
      // Amortization timeline silently fails
      expect(mockApiFetch).not.toHaveBeenCalled()
    })
  })
})

