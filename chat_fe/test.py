#create a matplotlib chart
import matplotlib.pyplot as plt
def create_chart():
    # Sample data
    x = [1, 2, 3, 4, 5]
    y = [2, 3, 5, 7, 11]

    # Create a line chart
    plt.plot(x, y, marker='o')

    # Add title and labels
    plt.title('Sample Line Chart')
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')

    return plt


plot = create_chart()
plot.savefig('chart.png')
